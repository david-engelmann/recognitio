#!/usr/bin/env python3
"""Pin the submission packs and the facts their evidence checks rest on.

The top 20 program prepared one submission pack per directory
for the Cursor Marketplace, the Claude plugin directory, and
the Agent Plugins portable package. Nothing in any pack has
been submitted, and each pack says so in a pinned sentence.
The claim check reads the packs the way the later build gates
read their briefs, on flattened lower case text with the
honest sentence lifted out first, so a filed or live listing
claim fails here in any case and in the ordinary wordings of
such a claim, and a promised review timeline fails with it,
since no primary source states one. Each pack also states the
version it was written against and the date its requirements
were read, and this gate holds both against the shipped
manifests, so a version bump or a stale pack fails here
instead of reaching a filing. The load bearing figures in
the pack prose stand pinned beside the sentences. The
Claude pack tree figures, its file count and its largest
file sizes and its credential scan count, stand pinned in
that same style, and the gate test suite measures them
against the tracked tree, so a tree that grows or shrinks
past the stated figures fails instead of drifting in
silence the way SC3 kept doing.

The figure half re-derives the load bearing figures in the
Claude pack from the tree itself. The file count, the largest
file and its size, the largest file that is not an image or a
font or a video and its size, the file count the credential scan
ran over, counted by the tree walk the scan itself reads,
with the scan itself, and the three frontmatter
description lengths the component check names all stand
measured against the tree on every run, so a falsified figure
fails here beside the strict control rather than standing
under the success line. A layout that does not hold the demo
recording is a partial layout and the tree figures are not
read from it, because a partial tree cannot falsify a figure
that names the whole one.

The evidence half pins the manifest facts the packs assert.
The Cursor marketplace file carries its required name and
owner and one entry, and the Cursor manifest carries the
description, author, and license the checklist asks about,
with the logo, skill, and rule paths resolving in the tree.
The Claude manifest carries the fields its evidence check
names, with its component paths resolving inside the folder,
its marketplace file carries the required name and owner,
and its recognitio entry matches the manifest in name,
source, and strict mode, beside the recognitio-mod entry
the same pack names with its own folder source and strict
mode. The portable manifest stays inside the closed
ten field set of the Agent Plugins specification and carries
the exact values the host listing would read from it. A
license file stands at the root the Claude pack names as
the plugin folder.

Exits nonzero with one line per problem when anything fails.
"""

import json
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

CURSOR_PACK = "docs/submission-cursor.md"
CLAUDE_PACK = "docs/submission-claude.md"
PORTABLE_PACK = "docs/submission-agent-plugins.md"
CLAUDE_PLUGIN = ".claude-plugin/plugin.json"
CLAUDE_MARKET = ".claude-plugin/marketplace.json"
CURSOR_PLUGIN = ".cursor-plugin/plugin.json"
CURSOR_MARKET = ".cursor-plugin/marketplace.json"
PORTABLE = "agent-plugins-package/plugin.json"

REPO_URL = "https://github.com/david-engelmann/recognitio"
SCHEMA_URL = "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json"
HONEST_SENTENCE = "nothing in this pack has been submitted."

PACK_ROUTES = {
    CURSOR_PACK: ("cursor.com/marketplace/publish",),
    CLAUDE_PACK: ("claude.ai/directory/manage",),
    PORTABLE_PACK: (
        "The Agent Plugins project runs no directory of packages.",
        "github/awesome-copilot",
        "plugins/external.json",
    ),
}

# Load bearing figures and promises in the pack prose. A
# drift in any of them is a falsified pack under a green
# gate, so each stands pinned word for word.
PACK_PINS = {
    CURSOR_PACK: (
        "must stay at or under 10 MB",
        "Every plugin is manually reviewed before it is listed",
    ),
    CLAUDE_PACK: (
        "at least 40 words",
        "must stay under 5 MiB",
        "holds 274 files",
        "held 267 files",
        "held 274 files",
        "at 274 files against a cap of 512 files",
        "demo recording at 24,222,065 bytes",
        "tests/test_gate_scripts.py at 375,816 bytes",
        "scan over all 274 files in the tree",
    ),
    PORTABLE_PACK: (
        "six month cycle",
    ),
}

COMMON_FRAGMENTS = (
    "Nothing in this pack has been submitted.",
    "Requirements were read from the primary sources named "
    "in this pack on 2026-10-27.",
    "## What remains David's act",
)

# Claims of a filed or live listing, read on the flattened
# lower case text with the honest sentence lifted out. A
# prepared pack must never carry one, in the same spirit as
# the stale wording refusals the other gates hold.
BANNED_CLAIMS = (
    "listing is live",
    "is now listed",
    "is listed in",
    "is listed on",
    "listed in the marketplace",
    "pack has been submitted",
    "was approved and listed",
    "approved for listing",
    "we filed",
    "filed the submission",
    "submission was filed",
    "has been filed",
    "is now live",
)

PACK_BANNED_CLAIMS = {
    CLAUDE_PACK: ("is available in the directory",),
    PORTABLE_PACK: (
        "runs a package registry",
        "runs a registry",
        "operates a directory",
    ),
}

# No primary source states a review timeline for any of the
# three routes, so a promised one fails in any pack, in
# digits or in number words.
TIMELINE_CLAIM = re.compile(
    r"within ([0-9]+|one|two|three|four|five|six|seven|"
    r"eight|nine|ten|fourteen|thirty|sixty|ninety) "
    r"(business )?(day|days|week|weeks)")

CLOSED_FIELDS = {
    "$schema", "name", "version", "description", "author",
    "homepage", "repository", "license", "keywords",
    "extensions",
}

NAME_PATTERN = re.compile(r"[a-z0-9]([a-z0-9.-]*[a-z0-9])?")
KEYWORD_PATTERN = re.compile(r"[a-z0-9]+(-[a-z0-9]+)*")


def semver_ok(value):
    """The house version shape, ASCII digits, no leading zeros."""
    if not isinstance(value, str):
        return False
    parts = value.split(".")
    if len(parts) != 3:
        return False
    for part in parts:
        if not part or not part.isascii() or not part.isdigit():
            return False
        if len(part) > 1 and part.startswith("0"):
            return False
    return True


class DuplicateKeyError(ValueError):
    """A JSON object names one key twice."""


def strict_json_loads(text):
    """Parse JSON refusing a repeated key and the loose constants."""
    def reject(pairs):
        seen = {}
        for key, value in pairs:
            if key in seen:
                raise DuplicateKeyError("repeated key %r" % (key,))
            seen[key] = value
        return seen

    def reject_constant(value):
        raise ValueError("loose JSON constant %r" % (value,))
    return json.loads(
        text, object_pairs_hook=reject,
        parse_constant=reject_constant)


def load_manifest(root, rel, problems):
    path = root / rel
    if path.exists() and not path.is_file():
        problems.append(
            "%s cannot be read, it is not a regular file" % rel)
        return None
    try:
        raw = path.read_text(encoding="utf-8")
    except OSError:
        problems.append("%s is missing" % rel)
        return None
    try:
        data = strict_json_loads(raw)
    except (ValueError, DuplicateKeyError) as exc:
        problems.append("%s does not parse, %s" % (rel, exc))
        return None
    if not isinstance(data, dict):
        problems.append("%s is not an object" % rel)
        return None
    return data


def author_name(data):
    author = data.get("author")
    if isinstance(author, dict):
        return author.get("name")
    return None


def field_problems(rel, data, field, problems, why):
    if not data.get(field):
        problems.append("%s carries no %s, %s" % (rel, field, why))


def license_problems(rel, data, problems):
    if data.get("license") != "MIT":
        problems.append(
            "%s carries license %r and the pack states MIT"
            % (rel, data.get("license")))


def owner_problems(rel, market, problems, why):
    owner = market.get("owner")
    if not isinstance(owner, dict) or not owner.get("name"):
        problems.append(
            "%s carries no owner name, %s" % (rel, why))


def entry_problems(rel, market, plugin, problems):
    entries = market.get("plugins")
    if not isinstance(entries, list) or len(entries) != 1:
        problems.append(
            "%s must list exactly one plugin entry" % rel)
        return None
    entry = entries[0]
    if not isinstance(entry, dict):
        problems.append("%s carries an entry that is not an object" % rel)
        return None
    if plugin is not None and entry.get("name") != plugin.get("name"):
        problems.append(
            "%s entry name %r does not match the manifest "
            "name %r" % (rel, entry.get("name"), plugin.get("name")))
    if plugin is not None:
        # The Cursor pack states the entry paths resolve
        # from the one plugin root, so this gate reads the
        # entry source, skills, and logo the way the Cursor
        # gate does and pins them to the manifest values.
        # An entry path written from another base resolves
        # nowhere under its own source, and a gate that
        # never opened those values would certify the pack
        # sentence in silence.
        if entry.get("source") != "./":
            problems.append(
                "%s entry carries source %r and the pack "
                "states the plugin root the manifest stands "
                "at" % (rel, entry.get("source")))
        if entry.get("skills") != plugin.get("skills"):
            problems.append(
                "%s entry carries skills %r and the manifest "
                "carries %r, so the entry paths do not "
                "resolve from the entry source"
                % (rel, entry.get("skills"), plugin.get("skills")))
        if entry.get("logo") != plugin.get("logo"):
            problems.append(
                "%s entry carries logo %r and the manifest "
                "carries %r"
                % (rel, entry.get("logo"), plugin.get("logo")))
    return entry


def claude_entry_problems(rel, market, plugin, problems):
    """The Claude listing holds the recognitio and mod entries.

    The recognitio entry comes back for the source and strict
    checks the caller runs, and the recognitio-mod entry is
    named here so a listing that lost it, or renamed it, or
    grew a third entry fails in this gate as well.
    """
    entries = market.get("plugins")
    if not isinstance(entries, list) or len(entries) != 2:
        problems.append(
            "%s must list exactly two plugin entries, the "
            "recognitio plugin and the recognitio-mod plugin"
            % rel)
        return None
    by_name = {}
    for entry in entries:
        if not isinstance(entry, dict):
            problems.append(
                "%s carries an entry that is not an object" % rel)
            return None
        by_name[entry.get("name")] = entry
    entry = by_name.get("recognitio")
    if entry is None:
        if plugin is not None:
            problems.append(
                "%s entry name %r does not match the manifest "
                "name %r"
                % (rel, entries[0].get("name"),
                   plugin.get("name")))
        else:
            problems.append(
                "%s lists no recognitio entry" % rel)
        return None
    if plugin is not None and entry.get("name") != plugin.get("name"):
        problems.append(
            "%s entry name %r does not match the manifest "
            "name %r" % (rel, entry.get("name"), plugin.get("name")))
    mod = by_name.get("recognitio-mod")
    if mod is None:
        problems.append(
            "%s lists no recognitio-mod entry, and the Claude "
            "pack names the mod entry beside the plugin entry"
            % rel)
    else:
        if mod.get("source") != "./plugins/recognitio-mod":
            problems.append(
                "%s recognitio-mod entry carries source %r and "
                "the pack states the mod plugin folder"
                % (rel, mod.get("source")))
        if mod.get("strict") is not True:
            problems.append(
                "%s recognitio-mod entry carries strict %r and "
                "the pack states strict mode on"
                % (rel, mod.get("strict")))
    return entry


# The media suffixes the largest plain file figure sets
# aside. The set held image and font suffixes until the
# video standard programme added the two video forms, and
# the pack sentence that names this class names all three
# classes with it.
MEDIA_SUFFIXES = {
    ".gif", ".png", ".svg", ".jpg", ".jpeg", ".ico",
    ".woff", ".woff2", ".ttf", ".otf", ".eot",
    ".mp4", ".webm",
}

DEMO_RECORDING = "docs/images/recognitio-cursor-agent-demo.gif"

# The demo recordings a largest file figure may name. The
# hero sessions ship as a GIF preview and as MP4 and WebM
# films, and the largest file in the tree is whichever of
# these forms weighs most, so the figure check holds the
# measured largest file to this set rather than to one
# form. The video standard programme made the Claude Code
# WebM the largest of them.
DEMO_RECORDINGS = {
    "docs/images/recognitio-claude-code-demo.gif",
    "docs/images/recognitio-claude-code-demo.mp4",
    "docs/images/recognitio-claude-code-demo.webm",
    "docs/images/recognitio-claude-code-demo-short.gif",
    "docs/images/recognitio-cursor-agent-demo.gif",
    "docs/images/recognitio-cursor-agent-demo.mp4",
    "docs/images/recognitio-cursor-agent-demo.webm",
}

# The private key header shape stands in the same spelling
# the extractor mask uses, any capitalised qualifier before
# the words PRIVATE KEY and the PGP block form beside the
# plain form, so the scan whose zero hits the pack asserts
# covers every header the mask would withhold.
CREDENTIAL_SCAN_PATTERNS = (
    re.compile(rb"-----BEGIN [A-Z0-9 ]*PRIVATE KEY"
               rb"(?: BLOCK)?-----"),
    re.compile(rb"(?:AKIA|ASIA)[0-9A-Z]{16}"),
    re.compile(rb"(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9]{20,}"),
    re.compile(rb"github_pat_[A-Za-z0-9_]{20,}"),
)


def tree_files(root):
    """Every file and link under a root, caches aside.

    The git directory and the bytecode caches stand aside,
    because neither is a file the pack describes and the
    caches come and go with every test run on a working tree.
    Sizes are read with lstat so a link counts at the length
    of its target spelling, the same size the tree listing
    records for it.
    """
    found = []
    for dirpath, dirnames, filenames in os.walk(root):
        for skipped in (".git", "__pycache__", ".pytest_cache"):
            if skipped in dirnames:
                dirnames.remove(skipped)
        # A link to a directory stands in the dirname list,
        # and a linked worktree carries its git pointer as a
        # file rather than a directory. The link is a file of
        # the tree and counts here, and the pointer is not.
        for name in list(dirnames):
            path = Path(dirpath) / name
            if path.is_symlink():
                dirnames.remove(name)
                try:
                    size = path.lstat().st_size
                except OSError:
                    continue
                found.append(
                    (path.relative_to(root).as_posix(), size))
        for name in filenames:
            if name.endswith(".pyc"):
                continue
            path = Path(dirpath) / name
            rel = path.relative_to(root).as_posix()
            if rel == ".git":
                continue
            try:
                size = path.lstat().st_size
            except OSError:
                continue
            found.append((rel, size))
    return sorted(found)


def frontmatter_description_length(root, rel):
    path = root / rel
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return None
    match = re.search(r"^description:\s*(.+)$", text, re.MULTILINE)
    if not match:
        return None
    return len(match.group(1).strip())


def tree_measurements(root):
    """The figures the Claude pack states, measured on one tree.

    Returns None on a partial layout, which is any root that
    does not hold the demo recording the largest file figure
    names, because no partial tree can stand for the whole one
    the figures describe.
    """
    files = tree_files(root)
    by_path = dict(files)
    if DEMO_RECORDING not in by_path:
        return None
    largest = max(files, key=lambda item: item[1])
    plain = [
        item for item in files
        if Path(item[0]).suffix.lower() not in MEDIA_SUFFIXES
    ]
    largest_plain = max(plain, key=lambda item: item[1])
    scan_hits = 0
    for rel, _size in files:
        try:
            data = (root / rel).read_bytes()
        except OSError:
            continue
        for pattern in CREDENTIAL_SCAN_PATTERNS:
            scan_hits += len(pattern.findall(data))
    return {
        "count": len(files),
        "largest_path": largest[0],
        "largest_size": largest[1],
        "largest_plain_path": largest_plain[0],
        "largest_plain_size": largest_plain[1],
        # The scan count is the length of this tree walk, the
        # set the scan reads, and the pack sentence names it
        # in those words rather than as a tracked file count.
        "paths": [rel for rel, _size in files],
        "scan_files": len(files),
        "scan_hits": scan_hits,
    }


NUMBER_UNITS = {
    "zero": 0, "one": 1, "two": 2, "three": 3, "four": 4,
    "five": 5, "six": 6, "seven": 7, "eight": 8, "nine": 9,
    "ten": 10, "eleven": 11, "twelve": 12, "thirteen": 13,
    "fourteen": 14, "fifteen": 15, "sixteen": 16,
    "seventeen": 17, "eighteen": 18, "nineteen": 19,
}
NUMBER_TENS = {
    "twenty": 20, "thirty": 30, "forty": 40, "fifty": 50,
    "sixty": 60, "seventy": 70, "eighty": 80, "ninety": 90,
}
FIGURE_TOKEN = re.compile(
    r"[A-Za-z]+|[0-9][0-9,]*(?:\.[0-9]+)?")

SENTENCE_ABBREVIATIONS = {
    "approx", "ca", "etc", "vs", "mr", "mrs", "dr", "st",
    "est",
}

DECIMAL_UNITS = {
    "byte", "bytes", "b", "octet", "octets", "kib", "kb",
    "mib", "mb", "gib", "characters", "chars", "glyphs",
    "files", "hits", "hundred", "thousand", "million",
    "billion",
}


def split_figure_sentences(text):
    """The sentences of a flattened text, abbreviation aware.

    A period after an abbreviation in the enumerated set,
    approx, ca, etc, vs, mr, mrs, dr, st and est, or after a
    single letter as c., ends no sentence, because the
    figure that follows the abbreviation belongs to the
    sentence that opened before it and is judged with it.
    """
    parts = []
    start = 0
    for match in re.finditer(r"[.!?]\s+", text):
        before = text[start:match.start()]
        word = re.search(r"([A-Za-z]+)$", before)
        if word and (
                word.group(1).lower() in SENTENCE_ABBREVIATIONS
                or len(word.group(1)) == 1):
            continue
        parts.append(text[start:match.start() + 1])
        start = match.end()
    if text[start:].strip():
        parts.append(text[start:])
    return [part.strip() for part in parts if part.strip()]


def figure_tokens(sentence):
    """The word and number tokens of one sentence.

    Dates, addresses and links are lifted out first, because
    the numbers inside them state no figure of the tree. A
    spelled out number is read as one span where its words
    run together, and the word no counts as zero where a
    figure noun, hit, hits or files, stands anywhere in the
    two tokens that follow it, the reading the priced
    figures themselves use for a zero result.
    """
    masked = re.sub(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", " ", sentence)

    def mask_decimal(match):
        # A decimal carrying a unit states a figure in that
        # unit, so it stands. A decimal with no unit after it
        # is a version or a date shape and states no figure.
        rest = masked_tail[match.end():].lstrip()
        word = re.match(r"[A-Za-z]+", rest)
        if match.group(0).count(".") == 1 and word and \
                word.group(0).lower() in DECIMAL_UNITS:
            return match.group(0)
        return " "

    masked_tail = masked
    masked = re.sub(
        r"[0-9]+(?:\.[0-9]+)+", mask_decimal, masked)
    masked = re.sub(r"\S+@\S+", " ", masked)
    masked = re.sub(r"https?://\S+", " ", masked)
    tokens = [
        match.group(0).lower()
        for match in FIGURE_TOKEN.finditer(masked)
    ]
    spans = []
    index = 0
    while index < len(tokens):
        token = tokens[index]
        if token[0].isdigit():
            plain = token.replace(",", "")
            value = float(plain) if "." in plain else int(plain)
            spans.append((index, index, value, token))
            index += 1
            continue
        if token == "no" and any(
                word in ("hit", "hits", "files")
                for word in tokens[index + 1:index + 3]):
            spans.append((index, index, 0, token))
            index += 1
            continue
        if token in NUMBER_UNITS or token in NUMBER_TENS or \
                token == "dozen" or (
                    token in ("a", "an") and index + 1 < len(tokens)
                    and tokens[index + 1] in (
                        "hundred", "thousand", "million",
                        "billion", "dozen")):
            total = 0
            current = 0
            end = index
            while end < len(tokens):
                word = tokens[end]
                if word in NUMBER_UNITS:
                    current += NUMBER_UNITS[word]
                elif word in NUMBER_TENS:
                    current += NUMBER_TENS[word]
                elif word in ("a", "an") and end == index:
                    current += 1
                elif word == "hundred" and current:
                    current *= 100
                elif word == "thousand" and current:
                    total += current * 1000
                    current = 0
                elif word == "million" and current:
                    total += current * 1000000
                    current = 0
                elif word == "billion" and current:
                    total += current * 1000000000
                    current = 0
                elif word == "dozen":
                    current = (current or 1) * 12
                elif word == "and" and (current >= 20 or total) and \
                        end + 1 < len(tokens) and (
                        tokens[end + 1] in NUMBER_UNITS
                        or tokens[end + 1] in NUMBER_TENS):
                    # The and of a spelled number joins only a
                    # number already standing at a tens value or
                    # past a thousand, so the two ends of a
                    # stated range, as zero and five, stay two
                    # spans and the range reading can judge them.
                    end += 1
                    continue
                else:
                    break
                end += 1
            spans.append(
                (index, end - 1, total + current,
                 " ".join(tokens[index:end])))
            index = end
            continue
        index += 1
    return tokens, spans


CAP_WORDS_BEFORE = {
    "cap", "capped", "caps", "maximum", "limit", "limited",
    "ceiling",
}
CAP_WORDS_AFTER = {"cap", "capped", "limit", "ceiling"}


def cap_governed(tokens, span):
    """Whether a number names a cap rather than a measurement.

    The pack states its figures against checklist caps, and
    a cap value in the same sentence is a limit the checklist
    holds, not a figure of this tree, so a number governed
    by a cap word stands outside the measured readings. The
    governing word may stand before the number in any of
    its forms, as a cap of a number, a value the repo is
    capped at, a checklist that caps the tree at a number,
    a tree limited to a number, or a maximum of a number, or
    right after the number and its unit, as a file limit a
    size stands under.
    """
    before = tokens[max(0, span[0] - 4):span[0]]
    after = tokens[span[1] + 1:span[1] + 4]
    return any(word in CAP_WORDS_BEFORE for word in before) or \
        any(word in CAP_WORDS_AFTER for word in after)


def bound_relation(tokens, span):
    """The comparison a number in a sentence is stated under.

    A figure stated as a bound is judged as the bound it
    states, so a true floor or ceiling passes and a false
    one fails. The words over and more than state a floor
    the measurement must pass, the words at least state one
    it must reach, and the words under, below, fewer than,
    less than, at most and up to state a ceiling in the same
    way. The negated forms invert the pair they open, so no
    fewer than and no less than state a floor and no more
    than states a ceiling. A bound stated after its number
    in the postfix forms, at most or at least standing after
    the number and its unit, or the pairs or more, or fewer
    or or less standing after the number and its unit, is
    read the same way. The
    single word bounds over, above, under and below are
    read only within three tokens of the span and not where
    the word all follows them in that window. A number with
    no bound word around it is stated as the figure itself.
    """
    window = tokens[max(0, span[0] - 6):span[0]]
    pairs = list(zip(window, window[1:]))
    # The negated bounds stand first, because the no that
    # opens them inverts the pair it stands before. No fewer
    # than and no less than state a floor the measurement
    # must reach, and no more than states the ceiling it
    # must stay under, so neither is read as the unnegated
    # pair inside it.
    if ("no", "more") in pairs:
        return "lte"
    if ("no", "fewer") in pairs or ("no", "less") in pairs:
        return "gte"
    if ("more", "than") in pairs:
        return "gt"
    if ("at", "least") in pairs:
        return "gte"
    if ("fewer", "than") in pairs or ("less", "than") in pairs:
        return "lt"
    if ("at", "most") in pairs:
        return "lte"
    if "up" in window and "to" in window:
        # The up of the tally marker added up to is the
        # marker its own word and not a bound, so a figure
        # stated under that marker is read as the tally
        # it states and not as a ceiling.
        up_at = len(window) - 1 - window[::-1].index("up")
        if not (up_at and window[up_at - 1] == "added"):
            return "lte"
    # A single bound word governs only the number it stands
    # right beside, so the over of a scan over all its files
    # and the under of a size under a limit stated later in
    # the sentence state no bound for a figure beside them.
    for word, relation in (
            ("over", "gt"), ("above", "gt"),
            ("under", "lt"), ("below", "lt")):
        if word in window:
            at = len(window) - 1 - window[::-1].index(word)
            if span[0] - (span[0] - len(window) + at) <= 3 and \
                    "all" not in window[at:]:
                return relation
    # A bound stated after its number, the postfix form, is
    # read from the words that follow the span and its unit,
    # so a figure stated as a number of files at most is a
    # ceiling in the same way as one stated as at most a
    # number of files.
    after = tokens[span[1] + 1:span[1] + 5]
    if after and after[0] in (
            "files", "file", "entries", "items", "bytes",
            "byte", "characters", "chars", "glyphs", "hits",
            "hit", "kib", "kb", "mib", "mb", "gib", "b",
            "octets"):
        after = after[1:]
    after_pairs = list(zip(after, after[1:]))
    if ("at", "most") in after_pairs:
        return "lte"
    if ("at", "least") in after_pairs:
        return "gte"
    if ("or", "fewer") in after_pairs or \
            ("or", "less") in after_pairs:
        return "lte"
    if ("or", "more") in after_pairs:
        return "gte"
    return None


def bound_holds(relation, claimed, measured):
    """Whether a measured value satisfies a stated bound."""
    if relation == "gt":
        return measured > claimed
    if relation == "gte":
        return measured >= claimed
    if relation == "lt":
        return measured < claimed
    if relation == "lte":
        return measured <= claimed
    return claimed == measured


def is_year_span(tokens, span):
    """Whether a digit span reads as a year rather than a figure.

    A four digit year with no quantity unit after it states
    a date, not a measurement, so the readings leave it
    standing. A year shaped number carrying a unit, as a
    count of that many files, is a figure and is judged.
    """
    if not span[3].isdigit() or "," in span[3]:
        return False
    if not 1900 <= span[2] <= 2099:
        return False
    unit = tokens[span[1] + 1] if span[1] + 1 < len(tokens) else ""
    return unit not in (
        "files", "hits", "hit", "bytes", "byte",
        "characters", "chars", "entries", "items")


def figure_problems(root, problems):
    """Check the Claude pack figures against the measured tree.

    The gate certifies an enumerated family and refuses
    outside it. The canonical priced figure statements, the
    forms the pack carries for the tree file count, the
    credential scan file count and result, the largest file
    and the largest plain file with their sizes, and the
    frontmatter description lengths, are judged on value,
    so every occurrence of a canonical statement must state
    the measured value for its quantity. Any other sentence
    that asserts one of those quantities, carrying the
    quantity its anchor nouns and unit words together with
    a value expression, a digit numeral, a decimal with a
    unit, a spelled out number, a fraction of a unit such
    as half a MiB, three quarters of a MiB or a fifth of a
    MiB, a percent of a unit in digits or spelled out or
    as per cent or per-cent, or as pct, per mille
    or per thousand, a percent sign standing
    after a spelled number counting in the spelled
    register in the same way, a percent stated
    against the size of a unit counting in the same
    way as one stated of the unit, a decimal stated
    against the size of a unit counting in the same
    way, or a decimal standing before of a unit
    with a leading point where it carries no digit before
    it, the article before the unit being a, an or the, or
    a vague magnitude word such as thousands,
    hundreds, dozens or scores, fails by name as an
    unpriced figure statement,
    whatever value it states. The gate does not judge the
    value of arbitrary prose. A figure stated as a bound is
    judged as the bound it states, with no fewer than read
    as a floor and no more than read as a ceiling, and a
    figure stated between two values is judged on value as
    the range it states, for the file count, the scan
    result, the largest file size, the largest plain file
    size and a description length.
    A figure governed by a cap word is a checklist limit
    rather than a measurement, except that a file count cap
    stated outside the canonical capped statement is itself
    judged against the cap the pack states, 512 files. A
    dated figure assertion stands exempt if and only
    if it passes the exemption test in the order stated
    here, the stated order being the order the reading
    holds. First, the assertion stands in a clause
    carrying a complete dating of its own, read at every
    grain present, the full date, a month and a year, or
    a year alone, with a range counting by both its ends
    and a date standing attributive before a noun
    counting as dating in the clause, there being no
    skip set. A sentence initial date phrase or stamp
    standing as its own clause directly before the
    assertion its clause is part of that clause its
    dating for this step. Second, every dating in that
    clause is a dating other than the pack measurement
    dating at its grain, and the clause carries one
    dating only, so a second dating is ambiguity and
    judges. Third, no measurement dating and no
    different dating stands in a governing position
    before the assertion in the sentence, in a preamble,
    a stamp, a label fragment glued from the line above
    in the flattened text, a range beginning, or an
    earlier clause, the governing before reading taking
    every dating that stands before the clause whatever
    opener it stands under, on, in, from or since among
    them, and whatever separator stands before the
    clause, a comma or a semicolon among them. An
    assertion inside a subordinate clause carrying its
    own dating, and an assertion in a clause that opens
    with its own date phrase, take their own dating at
    the third step, the earlier dating not governing
    them. The subordinate limb holds where the splitter
    separates the clause, and the splitter separates a
    relative clause at every grain the reading holds,
    the full date in either spelled order, a month and
    a year, and a year alone among them. The comma
    inside a spelled full date in the US order is part
    of the date and not a clause separator, and a
    resumption adverb standing between the relative
    dating and a listed verb does not defeat the
    separation, one adverb or two of them standing
    together, the adverbs being still, then, now,
    also, again, already, just, soon, later, finally,
    subsequently and reportedly. Where the
    splitter cannot separate the clause, the merged
    clause is judged whenever a measurement dating
    stands in the sentence in a governing, fragment or
    phrase form, so the remaining effect of that limit
    is the false failure cost declared below and not an
    escape. A measurement phrase anywhere in the sentence,
    a phrase of the as measured family, the measured,
    counted, tallied, totalled, totaled, enumerated
    or inventoried word standing in
    one of the twelve prepositions on, in, over, at,
    during, by, before, after, since, from, through or
    within, or of the read on, dated, as of or as at
    family, carrying a
    measurement dating, judges every assertion in the
    sentence except an assertion inside a subordinate
    clause that passes the test above, wherever the
    phrase stands in the sentence, and no fallback
    below rescues an assertion in a measurement
    phrased sentence. Failing the test, an assertion whose
    clause carries dating is judged on that dating, and
    an assertion whose clause carries none is judged on
    the dating of the sentence as a whole under the
    fallback, its own verb phrase date standing in its
    clause where it carries one, mixed dating in the
    whole including any measurement dating judging and
    a whole dating that is a single dating other than
    the measurement dating exempting it in a sentence
    carrying no measurement phrase. Fourth, the
    backstop at sentence level. An assertion that
    passes the steps above stands exempt only where no
    dating stands elsewhere in the sentence in a form
    that governs past its own clause. A pure dating
    clause standing after the assertion its clause, a
    trailing bare dating fragment among its forms, and
    a pure dating clause standing before the assertion
    with another clause between it and the assertion, a
    preamble, a stamp, a label or a range end among
    their forms, defeat the exemption for every
    assertion the dating could govern where the dating
    they carry is a measurement dating at its grain or
    a dating different from the assertion its own
    dating, a range counting by both its ends wherever
    its ends stand and a date standing attributive
    before a noun counting in the same way. A
    participial measurement phrase in one of the
    twelve prepositions named above
    defeats the exemption of every assertion outside a
    separated clause carrying its own complete dating
    other than the measurement dating, in the same way.
    A range clause standing after the assertion is
    read by both its ends in the same way, in its ISO
    and spelled forms, capitalised and lower case, and
    in the and between form, and a range standing
    inside another clause is read by both its ends in
    the same way. A trailing verbless fragment
    carrying a figure noun, the count, the tally, the
    total, the figure, the result, the number or the
    sum, and a date is a pure dating
    clause for this backstop, and a trailing
    participial fragment of the counted, tallied,
    totalled, totaled, enumerated, inventoried,
    taken or measuring family, an absolute count taken
    fragment, a nominal measurement fragment, a label
    fragment and a date headed fragment carrying a
    short nominal tail are fragments in the same way.
    A dating glued at a clause its end is a fragment
    where no finite verb stands before it in its
    clause, so a full independent clause carrying its
    dating in its content stands outside this reading
    whole in the spelled forms as in the ISO form. A
    pure dating clause standing directly before a
    subordinate clause or a clause opening with its
    own date phrase, after another clause of the
    sentence, is read here in the same way,
    because the steps above count nothing before
    those clauses, while a sentence initial preamble
    stands counted in the steps above. A dating
    standing in another
    clause in a form past these enumerated forms
    stands outside the backstop in the same way as a
    dating in the content of a full independent
    clause.
    One exception stands, and it is the whole of the
    exception. A measurement dating standing in a full
    independent clause, one carrying its own subject
    and its own verb and no figure, does not reach the
    other assertions of the sentence, the rechecked
    form standing as its priced form. Month and year
    dating and year alone dating count as dating at
    their granularity, so October 2026 is the
    measurement month and 2026 alone is the measurement
    year. The dating forms read are
    the ISO full date, the ISO month, the spelled full date in the form
    27 October 2026 or October 27 2026, a month and a
    year, and a year alone. The false failure cost of
    this rule is declared beside it. A genuinely
    historical figure is judged where measurement dating
    stands in a governing position for it or where which
    dating governs it is ambiguous, and a subordinate
    historical figure inside a measurement phrased
    sentence whose clause the splitter cannot separate
    is judged with the sentence, and a subordinate
    historical figure whose clause the splitter cannot
    separate is judged with its sentence under a plain
    preamble in the same way, and that cost is the
    price of closing the dated escapes in the other
    direction. One reading stands as the closing
    residual of the dating family. A measurement event
    narrated as a full independent clause standing
    beside a historically dated figure, the count was
    taken on the measurement date standing as one of
    its forms, is read as the rechecked form, a
    figureless event clause, and the figure stands
    exempt on its own dating, and telling that
    narration from a recheck is a judgement the prose
    does not settle. A number belonging to another
    quantity is not a priced figure.
    The scan result is anchored by the scan, credential,
    check, sweep, audit, verification or census words with
    any of its nouns, and by the screening, inspection,
    review, search or pattern match words in the same
    way, and by the probe or examination words in the
    same way, and by the survey or analysis words in
    the same way, and by the inventory, count or tally
    words in the same way, and by the listing,
    register, catalogue or catalog words in the same
    way, the nouns being
    results, findings, matches, positives, issues,
    outcomes or hits, and a bare hit or hits noun needs no
    anchor word at all in its clause. The description
    quantity is anchored by the word description or
    descriptions with a character unit and needs no named
    component, and a component word alone, skill, reviewer,
    agent or output, anchors it in the same way, as does
    the word summary. A sentence naming a priced
    subject outright, the demo recording as the demo
    recording, the hero recording, the demo, the
    recording, the demo GIF, the gif, the cursor agent
    demo, the capture, the video, the walkthrough, the
    screencast, the animation, the movie, the clip,
    the footage, the film,
    the reel, the trailer, the videotape, the
    showreel, the screencapture or the playback, or
    by the
    recording its file name, or the
    largest plain file by its path in full or in part, by
    its SKILL.md name or as the skill file, the
    instructions file or the skill
    beside a byte size, together with a size in any byte
    factor unit the reading holds, bytes or octets, or
    the abbreviated factors kib, kb, mib, mb or gib in
    any case, asserts that subject its priced size with
    no superlative anywhere in it. Such a sentence stands outside the canonical
    form, so it is refused as unpriced whatever value it
    states, in the same way as any other assertion
    outside the canonical form, unless it is stated as a
    bound or as a range, where the bound and range
    readings above judge it as the bound or the range it
    states. The anchor, noun and subject sets in these
    readings are enumerations, and a synonym or a name
    outside them asserts a priced quantity only where a
    generic reading stated here catches it, as a bare
    hits noun does for the scan result or a count verb
    over the repo or the tree does for the file count.
    Spelled out numbers are read up to billions,
    and that is the ceiling of the spelled reading. Value
    forms past the enumerated grammar stand as the declared
    boundary of the family. Indeterminate magnitude
    phrases that state no number, myriad, countless and
    loads of among them and their kin, state no
    determinate value and stand unjudged. Numeral forms
    outside the digit and spelled sets, Roman and
    fullwidth forms among them, state no figure the gate
    reads, and fraction denominators past tenths state no
    fraction the gate reads. Two forms past the grammar
    are read in part and fail safe rather than standing
    unjudged. A spelled number past billions that carries
    a readable cardinal, as five trillion, is read as
    that cardinal and refused as unpriced for it, while a
    form carrying no readable cardinal, as a trillion,
    states no figure the gate reads. An ordinal form in a
    value position is likewise read as the cardinal or
    the digits it carries and refused for that value,
    while an ordinal standing as a modifier, as the repo
    its 9,999th file, states no value the gate reads.
    On a whole layout, a
    priced figure whose canonical statement stands absent,
    or reworded out of the canonical wording, fails by name
    as unverifiable rather than passing in silence, because
    a figure the gate cannot read is a figure no success
    line may stand over.
    """
    path = root / CLAUDE_PACK
    try:
        raw = path.read_text(encoding="utf-8")
    except OSError:
        return
    text = re.sub(r"\s+", " ", raw)
    measured = tree_measurements(root)
    whole = measured is not None

    def unverifiable(figure):
        problems.append(
            "%s states no %s the gate can verify, so that "
            "figure stands unverifiable"
            % (CLAUDE_PACK, figure))

    # Every figure reading is case insensitive and reads the
    # comma grouped form of a number beside the plain form,
    # because a falsified restatement does not announce itself
    # by matching the canonical capitalisation or grouping.
    # A figure is priced in any of the phrasings its reading
    # names, so a second statement in a sibling phrasing is
    # checked against the same measurement as the first.
    number = r"([0-9][0-9,]*)"

    def claimed_number(token):
        return int(token.replace(",", ""))

    descriptions = (
        frontmatter_description_length(
            root, ".agents/skills/recognitio/SKILL.md"),
        frontmatter_description_length(root, "agents/reviewer.md"),
        frontmatter_description_length(
            root, "output-styles/packet.md"),
    )
    desc_matches = list(re.finditer(
        r"the skill at %s characters and the reviewer "
        r"agent at %s characters and the output style "
        r"at %s characters" % (number, number, number),
        text, re.IGNORECASE))
    if whole and not desc_matches:
        unverifiable("frontmatter description lengths figure")
    for desc in desc_matches:
        claimed = tuple(
            claimed_number(group) for group in desc.groups())
        if None not in descriptions and claimed != descriptions:
            problems.append(
                "%s states frontmatter description lengths of "
                "%s characters and the tree measures %s"
                % (CLAUDE_PACK, claimed, descriptions))
    if not whole:
        return
    holds_matches = list(re.finditer(
        r"\b(?:the )?(?:repo|repository) holds %s files" % number,
        text, re.IGNORECASE))
    if not holds_matches:
        unverifiable("repo file count figure")
    for holds in holds_matches:
        if claimed_number(holds.group(1)) != measured["count"]:
            problems.append(
                "%s states the repo holds %s files and the tree "
                "holds %d" % (CLAUDE_PACK, holds.group(1),
                              measured["count"]))
    capped_matches = list(re.finditer(
        r"at %s files against a cap of 512 files" % number,
        text, re.IGNORECASE))
    if not capped_matches:
        unverifiable("capped file count figure")
    for capped in capped_matches:
        if claimed_number(capped.group(1)) != measured["count"]:
            problems.append(
                "%s states %s files against the cap and the tree "
                "holds %d" % (CLAUDE_PACK, capped.group(1),
                              measured["count"]))
    largest_matches = list(re.finditer(
        r"largest file is the demo recording at ([0-9,]+) bytes",
        text, re.IGNORECASE))
    if not largest_matches:
        unverifiable("largest file figure")
    for largest in largest_matches:
        claimed = int(largest.group(1).replace(",", ""))
        if measured["largest_path"] not in DEMO_RECORDINGS or \
                claimed != measured["largest_size"]:
            problems.append(
                "%s states the largest file is the demo "
                "recording at %s bytes and the tree measures "
                "%s at %d bytes"
                % (CLAUDE_PACK, largest.group(1),
                   measured["largest_path"], measured["largest_size"]))
    plain_matches = list(re.finditer(
        r"largest file that is not an image or a font or a "
        r"video is (\S+) at ([0-9,]+) bytes", text, re.IGNORECASE))
    if not plain_matches:
        unverifiable("largest plain file figure")
    for plain in plain_matches:
        claimed = int(plain.group(2).replace(",", ""))
        if plain.group(1) != measured["largest_plain_path"] or \
                claimed != measured["largest_plain_size"]:
            problems.append(
                "%s states the largest file that is not an "
                "image or a font or a video is %s at %s bytes "
                "and the tree measures %s at %d bytes"
                % (CLAUDE_PACK, plain.group(1), plain.group(2),
                   measured["largest_plain_path"],
                   measured["largest_plain_size"]))
    scan_matches = list(re.finditer(
        r"credential pattern scan over all %s files "
        r"in the tree" % number, text, re.IGNORECASE))
    if not scan_matches:
        unverifiable("credential scan file count figure")
    for scan in scan_matches:
        if claimed_number(scan.group(1)) != measured["scan_files"]:
            problems.append(
                "%s states the credential pattern scan ran over "
                "%s files in the tree and the tree walk counts %d"
                % (CLAUDE_PACK, scan.group(1),
                   measured["scan_files"]))
    # The scan result stands under the same discipline as the
    # other figures. Every statement of its hit count is read
    # and checked against the measured count, so a true first
    # statement cannot carry a falsified second one past the
    # gate, and on a whole layout no readable statement at all
    # fails as unverifiable rather than passing as a presence.
    result_matches = list(re.finditer(
        r"(?:returned|found) ([0-9][0-9,]*|zero|no) hits?\b",
        text, re.IGNORECASE))
    if not result_matches:
        unverifiable("credential scan result figure")
    for result in result_matches:
        token = result.group(1)
        if token.lower() in ("zero", "no"):
            claimed_result = 0
        else:
            claimed_result = claimed_number(token)
        if claimed_result != measured["scan_hits"]:
            problems.append(
                "%s states the credential pattern scan returned "
                "%s hits and the scan over this tree returns %d"
                % (CLAUDE_PACK, token, measured["scan_hits"]))
    # The inverted sentence reading. The canonical readings
    # above judge the canonical priced figure statements on
    # value. Every other sentence is read only to refuse it.
    # A sentence that asserts a priced quantity, carrying
    # the quantity its anchor nouns or unit words together
    # with a value expression, a digit numeral, a decimal
    # with a unit, a spelled out number or a vague magnitude
    # word, fails by name as an unpriced figure statement,
    # whatever value it states, so the gate never judges the
    # value of arbitrary prose. A figure stated as a bound
    # is judged as the bound it states, a figure governed by
    # a cap word is a checklist limit and not a measurement,
    # a dated sentence states the measurement of its date,
    # and a number belonging to another quantity, a version,
    # a folder count, a prompt allowance, a neighbouring
    # file or a second largest figure, is not a priced
    # figure. One carryover stands. A sentence that names a
    # priced quantity and states no value for it, followed
    # at once by a sentence that states a value and names
    # no quantity, is read as one assertion across the pair
    # and the second sentence is refused for the quantity
    # the first one named.
    sentences = split_figure_sentences(text)
    segments_of = lambda sentence: re.split(
        r", |; | and | while | but ", sentence)
    byte_factors = {
        "byte": 1, "bytes": 1, "b": 1, "octet": 1,
        "octets": 1, "kib": 1024, "kb": 1000,
        "mib": 1024 ** 2, "mb": 1000 ** 2, "gib": 1024 ** 3,
    }
    competing_units = {
        "bytes", "byte", "kib", "kb", "mib", "mb", "gib",
        "b", "octets", "characters", "chars", "glyphs",
        "hits", "hit", "words", "folders", "folder",
        "pixels", "pixel", "examples", "severities",
        "fields", "entries", "items", "urls", "listing",
        "working", "component", "components", "part",
        "parts", "section", "sections", "step", "steps",
        "kind", "kinds", "type", "types",
    }
    hit_nouns = {
        "hit", "hits", "result", "results", "finding",
        "findings", "match", "matches", "positive",
        "positives", "issue", "issues", "outcome",
        "outcomes",
    }
    vague_words = {
        "thousands", "hundreds", "dozens", "scores",
        "millions", "billions", "thousand", "hundred",
        "million", "billion", "dozen", "score",
    }
    multipliers = {
        "hundred": 100, "thousand": 1000,
        "million": 1000000, "billion": 1000000000,
    }

    count_verbs = {
        "holds", "held", "contains", "comprises", "totals",
        "total", "stands", "has", "have", "covered", "covers",
        "tracks", "tracked",
    }
    linking_words = {
        "in", "of", "the", "a", "an", "repo", "repository",
        "tree", "is", "are", "was", "were", "stands", "stood",
        "comes", "came", "come", "to", "at", "total", "count",
        "number", "numbering", "by", "on", "all", "for",
    }

    def unpriced(label, stated):
        problems.append(
            "%s carries an unpriced figure statement, a %s "
            "stated as %s outside the canonical form the gate "
            "judges on value" % (CLAUDE_PACK, label, stated))

    def canonical_covered(sentence):
        covered = {
            "count": set(), "scan": set(), "largest": set(),
            "plain": set(), "desc": set(),
        }
        for match in re.finditer(
                r"\b(?:the )?(?:repo|repository) holds (%s) files"
                % number, sentence, re.IGNORECASE):
            covered["count"].add(claimed_number(match.group(1)))
        for match in re.finditer(
                r"at (%s) files against a cap of 512 files"
                % number, sentence, re.IGNORECASE):
            covered["count"].add(claimed_number(match.group(1)))
        for match in re.finditer(
                r"credential pattern scan over all (%s) files "
                r"in the tree" % number, sentence, re.IGNORECASE):
            covered["count"].add(claimed_number(match.group(1)))
        for match in re.finditer(
                r"largest file is the demo recording at "
                r"([0-9,]+) bytes", sentence, re.IGNORECASE):
            covered["largest"].add(
                int(match.group(1).replace(",", "")))
        for match in re.finditer(
                r"largest file that is not an image or a font "
                r"or a video is (\S+) at ([0-9,]+) bytes",
                sentence, re.IGNORECASE):
            covered["plain"].add(
                int(match.group(2).replace(",", "")))
        for match in re.finditer(
                r"the skill at (%s) characters and the reviewer "
                r"agent at (%s) characters and the output style "
                r"at (%s) characters" % (number, number, number),
                sentence, re.IGNORECASE):
            for group in match.groups():
                covered["desc"].add(claimed_number(group))
        for match in re.finditer(
                r"(?:returned|found) ([0-9][0-9,]*|zero|no) "
                r"hits?\b", sentence, re.IGNORECASE):
            token = match.group(1)
            covered["scan"].add(
                0 if token.lower() in ("zero", "no")
                else claimed_number(token))
        return covered

    def desc_target(tokens, span):
        anchors = []
        if "skill" in tokens:
            anchors.append(
                (tokens.index("skill"), descriptions[0]))
        reviewer_at = None
        if "reviewer" in tokens:
            reviewer_at = tokens.index("reviewer")
        elif "agent" in tokens:
            reviewer_at = tokens.index("agent")
        if reviewer_at is not None:
            anchors.append((reviewer_at, descriptions[1]))
        if "output" in tokens and "style" in tokens:
            anchors.append(
                (tokens.index("output"), descriptions[2]))
        if anchors:
            _at, length = min(
                anchors,
                key=lambda anchor: min(
                    abs(span[0] - anchor[0]),
                    abs(span[1] - anchor[0])))
            return length
        if None not in descriptions:
            return sum(descriptions)
        return None

    def largest_target(tokens):
        if "plain" in tokens or (
                "not" in tokens and "image" in tokens):
            return (
                measured["largest_plain_path"],
                measured["largest_plain_size"],
                "largest plain file")
        return (
            measured["largest_path"],
            measured["largest_size"], "largest file")

    def largest_anchor(tokens):
        if any(word in tokens for word in (
                "largest", "biggest", "heaviest", "weightiest")):
            return True
        if "sizeable" in tokens or "sizable" in tokens:
            return True
        for i in range(len(tokens) - 3):
            if tokens[i:i + 4] == [
                    "top", "file", "by", "size"]:
                return True
        return False

    def ordinal_before(tokens):
        at = [
            i for i, word in enumerate(tokens)
            if word in (
                "largest", "biggest", "heaviest", "weightiest",
                "sizeable", "sizable")]
        if not at:
            return False
        before = tokens[max(0, at[0] - 3):at[0]]
        return any(word in before for word in (
            "second", "third", "fourth", "fifth"))

    # The pack its measurement date, the date its
    # requirements were read, against which a dated sentence
    # is told from a historical one.
    read_match = re.search(
        r"requirements were read from the primary sources "
        r"named in this pack on ([0-9]{4}-[0-9]{2}-[0-9]{2})",
        text, re.IGNORECASE)
    pack_date = read_match.group(1) if read_match else None
    pack_year = int(pack_date[:4]) if pack_date else None

    month_numbers = {
        "january": 1, "february": 2, "march": 3, "april": 4,
        "may": 5, "june": 6, "july": 7, "august": 8,
        "september": 9, "october": 10, "november": 11,
        "december": 12,
    }
    month_words = set(month_numbers)
    pack_month = int(pack_date[5:7]) if pack_date else None
    month_alt = "|".join(sorted(month_numbers))
    # The date forms as one alternation, held in one
    # place for the readings that search with it, the
    # measurement phrase reading and the fragment
    # reading among them. The month alternation stands
    # grouped inside each form, because an ungrouped
    # alternation would split the forms at its own bars
    # and a month grain form would read as its month
    # word alone and judge nothing.
    date_alt = (
        r"[0-9]{4}-[0-9]{2}-[0-9]{2}"
        r"|[0-9]{4}-[0-9]{2}\b"
        r"|[0-9]{1,2} (?:%s) [0-9]{4}"
        r"|(?:%s) [0-9]{1,2},? [0-9]{4}"
        r"|(?:%s) [0-9]{4}"
        r"|[0-9]{4}") % (month_alt, month_alt, month_alt)

    def dating_list(fragment):
        # Every dating expression in a fragment, at its own
        # granularity, as (key, is measurement) pairs. Full
        # dates are consumed first, so the month and year
        # inside one are not read again at a coarser grain.
        # A date standing attributive before a noun counts
        # as dating in the fragment, so no date is skipped
        # for the noun that follows it.
        work = fragment.lower()
        found = []

        def scan(pattern, build):
            nonlocal work
            out = []
            pieces = []
            last = 0
            for match in re.finditer(pattern, work):
                out.append(build(match))
                pieces.append(work[last:match.start()])
                pieces.append(" " * len(match.group(0)))
                last = match.end()
            pieces.append(work[last:])
            work = "".join(pieces)
            return out

        found += scan(
            r"\b[0-9]{4}-[0-9]{2}-[0-9]{2}\b",
            lambda m: (("full", m.group(0)),
                       pack_date is not None
                       and m.group(0) == pack_date))
        found += scan(
            r"\b([0-9]{1,2}) (%s) ([0-9]{4})\b" % month_alt,
            lambda m: (("full", "%s-%02d-%02d" % (
                m.group(3), month_numbers[m.group(2)],
                int(m.group(1)))),
                pack_date is not None and "%s-%02d-%02d" % (
                    m.group(3), month_numbers[m.group(2)],
                    int(m.group(1))) == pack_date))
        found += scan(
            r"\b(%s) ([0-9]{1,2}),? ([0-9]{4})\b" % month_alt,
            lambda m: (("full", "%s-%02d-%02d" % (
                m.group(3), month_numbers[m.group(1)],
                int(m.group(2)))),
                pack_date is not None and "%s-%02d-%02d" % (
                    m.group(3), month_numbers[m.group(1)],
                    int(m.group(2))) == pack_date))
        found += scan(
            r"\b([0-9]{4})-([0-9]{2})\b",
            lambda m: (("month", m.group(1),
                        int(m.group(2))),
                       pack_year is not None
                       and int(m.group(1)) == pack_year
                       and int(m.group(2)) == pack_month))
        found += scan(
            r"\b(%s) ([0-9]{4})\b" % month_alt,
            lambda m: (("month", m.group(2),
                        month_numbers[m.group(1)]),
                       pack_year is not None
                       and int(m.group(2)) == pack_year
                       and month_numbers[m.group(1)] == pack_month))
        c_tokens, c_spans = figure_tokens(work)
        for span in c_spans:
            if is_year_span(c_tokens, span):
                found.append(
                    (("year", span[2]),
                     pack_year is not None
                     and span[2] == pack_year))
        return found

    def initial_dating(fragment):
        # The dating a fragment opens with, in a date phrase
        # or a Dated, Measured or Read on stamp, as a single
        # governing dating, or an empty list where the
        # fragment opens with no dating.
        s = fragment.strip().lower()
        stamp = re.match(r"(dated|measured|read)\b[^,;]*", s)
        if stamp:
            found = dating_list(stamp.group(0))
            return found[:1]
        rest = s
        for _ in range(4):
            word = re.match(
                r"(on|in|as|of|from|over|during|by|before|"
                r"after|since|and|while|but|at)\s+", rest)
            if not word:
                break
            rest = rest[word.end():]
        for pattern, build in (
                (r"[0-9]{4}-[0-9]{2}-[0-9]{2}\b",
                 lambda m: (("full", m.group(0)),
                            pack_date is not None
                            and m.group(0) == pack_date)),
                (r"([0-9]{4})-([0-9]{2})\b",
                 lambda m: (("month", m.group(1),
                             int(m.group(2))),
                            pack_year is not None
                            and int(m.group(1)) == pack_year
                            and int(m.group(2))
                            == pack_month)),
                (r"([0-9]{1,2}) (%s) ([0-9]{4})\b" % month_alt,
                 lambda m: (("full", "%s-%02d-%02d" % (
                     m.group(3), month_numbers[m.group(2)],
                     int(m.group(1)))),
                     pack_date is not None
                     and "%s-%02d-%02d" % (
                         m.group(3), month_numbers[m.group(2)],
                         int(m.group(1))) == pack_date)),
                (r"(%s) ([0-9]{1,2}),? ([0-9]{4})\b" % month_alt,
                 lambda m: (("full", "%s-%02d-%02d" % (
                     m.group(3), month_numbers[m.group(1)],
                     int(m.group(2)))),
                     pack_date is not None
                     and "%s-%02d-%02d" % (
                         m.group(3), month_numbers[m.group(1)],
                         int(m.group(2))) == pack_date)),
                (r"(%s) ([0-9]{4})\b" % month_alt,
                 lambda m: (("month", m.group(2),
                             month_numbers[m.group(1)]),
                            pack_year is not None
                            and int(m.group(2)) == pack_year
                            and month_numbers[m.group(1)]
                            == pack_month)),
                (r"([0-9]{4})\b",
                 lambda m: (("year", int(m.group(1))),
                            pack_year is not None
                            and int(m.group(1)) == pack_year))):
            match = re.match(pattern, rest)
            if match:
                return [build(match)]
        return []

    def split_dating_clauses(sentence):
        # Clause like segments of one sentence, each with
        # the separator that stands before it and whether
        # it opens as a subordinate relative clause. The
        # and of a between range joins the two ends of one
        # assertion and splits nothing.
        raw = []
        seps = []
        offsets = []
        start = 0
        pattern = re.compile(r", |; | and | while | but ")
        for match in pattern.finditer(sentence):
            if match.group(0) == ", ":
                # The comma inside a spelled full date in
                # the US order is part of the date and not
                # a clause separator, so the date stands
                # whole in one segment for the readings
                # that search it.
                if re.search(
                        r"(?:%s) [0-9]{1,2}$" % month_alt,
                        sentence[:match.start()],
                        re.IGNORECASE) and re.match(
                        r"[0-9]{4}\b",
                        sentence[match.end():]):
                    continue
            if match.group(0) == " and ":
                current = sentence[start:match.start()]
                if "between" in current.lower():
                    tail = current.lower().rsplit(
                        "between", 1)[1]
                    after = sentence[match.end():]
                    if any(ch.isdigit() for ch in tail) and \
                            after[:1].isdigit():
                        continue
            raw.append(sentence[start:match.start()])
            seps.append(match.group(0))
            offsets.append(start)
            start = match.end()
        raw.append(sentence[start:])
        offsets.append(start)
        clauses = []
        for index, clause in enumerate(raw):
            sep = seps[index - 1] if index else ""
            subordinate = clause.strip().lower().startswith(
                ("that ", "which ", "who "))
            clauses.append(
                [clause, sep, subordinate, offsets[index]])
        # A relative clause can stand inside its own
        # segment and end where the main predicate resumes
        # after the relative clause its date, as a tree
        # that held a figure on a date contained another.
        # The relative part and the resumed main assertion
        # are then two assertions, the relative one
        # subordinate and the resumed one of the main
        # clause, so each takes its own governing dating.
        expanded = []
        main_verbs = (
            "contained", "contains", "held", "holds",
            "stands", "stood", "weighs", "weighed", "runs",
            "takes", "totals", "is", "was", "has", "have",
            "had", "counted", "numbered")
        for clause, sep, subordinate, clause_off in clauses:
            rel = re.search(
                r" (that|which|who) ", clause.lower())
            done = False
            if rel:
                after_rel = clause[rel.end():]
                # The date search takes every date form
                # the reading holds, the ISO full date,
                # the spelled full date in both orders, a
                # month and a year, and a year alone, from
                # the one alternation the readings share,
                # so a relative clause dated at any grain
                # is separated in the same way as its ISO
                # dated twin.
                for date_match in re.finditer(
                        date_alt, after_rel):
                    rest = after_rel[date_match.end():].lstrip()
                    # A resumption adverb standing between
                    # the relative dating and the listed
                    # verb is part of the resumption and
                    # does not defeat the separation, and
                    # two of them standing together are
                    # part of it in the same way.
                    verb = re.match(
                        r"(?:(?:still|then|now|also|again|"
                        r"already|just|soon|later|finally|"
                        r"subsequently|reportedly)"
                        r"\s+){0,2}(%s)\b" % "|".join(main_verbs),
                        rest)
                    if verb:
                        cut = rel.end() + date_match.end()
                        rel_part = clause[rel.start() + 1:cut]
                        main_part = clause[:rel.start()] + " " + \
                            clause[cut:].lstrip()
                        expanded.append(
                            [rel_part, sep, True, clause_off])
                        expanded.append(
                            [main_part, " ", subordinate,
                             clause_off])
                        done = True
                        break
            if not done:
                expanded.append(
                    [clause, sep, subordinate, clause_off])
        return expanded

    def pure_dating_clause(clause):
        # Whether a clause is a date phrase or a stamp and
        # nothing else, a preamble standing as its own
        # clause directly before an assertion. Its dating
        # is then part of the assertion its clause its
        # dating under the first step of the exemption
        # test. The dating forms and the opener and stamp
        # words are blanked and nothing may stand beside
        # them.
        work = clause.lower()
        work = re.sub(
            r"[0-9]{4}-[0-9]{2}-[0-9]{2}", " ", work)
        work = re.sub(r"\b[0-9]{4}-[0-9]{2}\b", " ", work)
        work = re.sub(
            r"\b[0-9]{1,2} (%s) [0-9]{4}\b" % month_alt,
            " ", work)
        work = re.sub(
            r"\b(%s) [0-9]{1,2},? [0-9]{4}\b" % month_alt,
            " ", work)
        work = re.sub(
            r"\b(%s) [0-9]{4}\b" % month_alt, " ", work)
        work = re.sub(r"\b[0-9]{4}\b", " ", work)
        work = re.sub(
            r"\b(on|in|as|of|from|since|over|during|by|"
            r"before|after|to|and|at|dated|measured|read)\b",
            " ", work)
        return not work.strip(" .,;")

    def fragment_dating(clause):
        # The dating standing in a fragment of a clause,
        # for the sentence level backstop. A clause that
        # is a date phrase or a stamp and nothing else is
        # a fragment whole. A range standing in a clause
        # is read by both its ends, a trailing clause
        # that is nothing but a range among its forms. A
        # trailing verbless fragment carrying a figure
        # noun and a date, a participial fragment of the
        # counted, tallied, totalled, totaled,
        # enumerated, inventoried, taken or measuring
        # family, an
        # absolute count taken fragment, a nominal
        # measurement fragment, a label fragment, an
        # attributive date fragment and a date headed
        # fragment carrying a short nominal tail are
        # fragments in the same way. A date phrase glued
        # at the
        # end of a clause, standing after a capitalised
        # opener word or opening with a capitalised month
        # at the clause its end, is a fragment at that
        # end, the label fragment glued from the line
        # above standing in this form, where no finite
        # verb stands before it in its clause. A dating
        # standing
        # inside the clause its content, after a lower
        # case opener or a verb, is no fragment, so a
        # full independent clause carrying its dating in
        # its content stands outside this reading whole.
        if pure_dating_clause(clause):
            return dating_list(clause)
        text = clause.strip()
        lowered = text.lower().rstrip(".")
        preps = (
            r"on|in|over|at|during|by|before|after|"
            r"since|from|through|within")
        range_match = re.search(
            r"\bbetween\s+(%s)\s+and\s+(%s)"
            % (date_alt, date_alt), text, re.IGNORECASE)
        if range_match:
            return dating_list(range_match.group(0))
        to_match = re.search(
            r"\b(%s)\s+to\s+(%s)\.?$"
            % (date_alt, date_alt), text, re.IGNORECASE)
        if to_match:
            return dating_list(to_match.group(0))
        fragment_patterns = (
            r"(?:the\s+)?(?:count|tally|total|figure|"
            r"result|number|sum)"
            r"\s+(?:%s)\s+(?:%s)",
            r"(?:recount|recheck|count|tally|"
            r"measurement|scan|check)\s+(?:%s)",
            r"(?:the\s+|a\s+|an\s+)?(?:%s)\s+"
            r"(?:recount|recheck|count|tally|"
            r"measurement|scan|check)",
            r"(?:with\s+)?(?:the\s+)?count\s+having\s+"
            r"been\s+taken\s+(?:%s)\s+(?:%s)",
            r"(?:with\s+)?(?:the\s+)?count\s+taken"
            r"\s+(?:%s)\s+(?:%s)",
            r"taken\s+(?:%s)\s+(?:%s)",
            r"counted\s+(?:%s)\s+(?:%s)",
            r"measuring\b.*\s(?:%s)\s+(?:%s)",
            r"(?:a|an|the)\s+measurement\s+(?:%s)"
            r"\s+(?:%s)",
            r"tallied\s+(?:%s)\s+(?:%s)",
            r"totalled\s+(?:%s)\s+(?:%s)",
            r"totaled\s+(?:%s)\s+(?:%s)",
            r"enumerated\s+(?:%s)\s+(?:%s)",
            r"inventoried\s+(?:%s)\s+(?:%s)",
        )
        checks = (
            fragment_patterns[0] % (preps, date_alt),
            fragment_patterns[1] % (date_alt,),
            fragment_patterns[2] % (date_alt,),
            fragment_patterns[3] % (preps, date_alt),
            fragment_patterns[4] % (preps, date_alt),
            fragment_patterns[5] % (preps, date_alt),
            fragment_patterns[6] % (preps, date_alt),
            fragment_patterns[7] % (preps, date_alt),
            fragment_patterns[8] % (preps, date_alt),
            fragment_patterns[9] % (preps, date_alt),
            fragment_patterns[10] % (preps, date_alt),
            fragment_patterns[11] % (preps, date_alt),
            fragment_patterns[12] % (preps, date_alt),
            fragment_patterns[13] % (preps, date_alt),
        )
        for pattern in checks:
            if re.fullmatch(pattern, lowered):
                return dating_list(lowered)
        headed = re.match(
            r"(?:on|in|at|as|of|from|since|over|during|"
            r"by|before|after)\s+(%s)\s+(.+)$" % date_alt,
            lowered)
        if headed:
            tail = re.findall(r"[A-Za-z]+", headed.group(2))
            finite = {
                "was", "were", "is", "are", "has", "have",
                "had", "seemed", "stood", "held", "holds",
                "contained", "contains", "reached",
                "recorded", "archived", "rechecked", "ran",
                "read", "opened", "took", "became",
            }
            if len(tail) <= 4 and not any(
                    word in finite for word in tail) and \
                    not any(ch.isdigit()
                            for ch in headed.group(2)):
                return dating_list(lowered)
        match = re.search(
            r"(%s)\.?$" % date_alt, text, re.IGNORECASE)
        if not match:
            return []
        before = text[:match.start()].rstrip()
        tokens = re.findall(r"[A-Za-z]+", before)
        finite = {
            "was", "were", "is", "are", "has", "have",
            "had", "seemed", "stands", "stood", "held",
            "holds", "contained", "contains", "reached",
            "recorded", "archived", "rechecked", "ran",
            "read", "opened", "counted", "numbered",
            "weighed", "takes", "took", "became",
            "remained", "closed", "showed",
        }
        if any(token.lower() in finite for token in tokens):
            return []
        if match.group(0)[:1].isupper():
            return dating_list(text[match.start():])
        if tokens and tokens[-1] in (
                "On", "In", "At", "From", "Since", "By",
                "Dated", "Measured", "Read"):
            return dating_list(text[match.start():])
        if len(tokens) >= 2 and tokens[-2:] == ["As", "of"]:
            return dating_list(text[match.start():])
        if tokens and tokens[-1].lower() in (
                "recount", "recheck", "count", "tally",
                "measurement", "scan", "check"):
            # A label word standing directly before the
            # date is a label fragment at the end of the
            # clause in the same way, the form the label
            # fragment glued from the line above takes in
            # the flattened text, where the clause before
            # it runs on into the label with no separator
            # the splitter reads.
            return dating_list(text[match.start():])
        return []

    def clause_has_figure(clause):
        c_tokens, c_spans = figure_tokens(clause)
        if any(
                not is_year_span(c_tokens, span)
                for span in c_spans):
            return True
        if any(word in vague_words for word in c_tokens):
            return True
        return re.search(
            r"\b(half|quarter|quarters|third|thirds)\b",
            clause.lower()) is not None

    carry = None
    carry_largest = None
    carry_grace = False
    for sentence in sentences:
        # The dated exemption under the rule stated in the
        # docstring. An exempt clause is dropped from the
        # sentence and the rest is judged as written.
        clauses = split_dating_clauses(sentence)
        # A measurement phrase anywhere in the sentence
        # judges every assertion that is not exempt under
        # the test below, so no fallback exemption stands
        # in a sentence carrying one. A measurement phrase
        # is a phrase of the family named in the docstring
        # carrying a measurement dating at its grain, so
        # the dating standing after each phrase is read
        # and the phrase counts only where that dating is
        # the measurement dating.
        # The measured, counted, tallied, totalled,
        # totaled, enumerated or inventoried word
        # standing in one
        # of the twelve prepositions on, in, over, at,
        # during, by, before, after, since, from, through
        # or within carries the phrase, at and during
        # among them, so a phrase in a preposition inside
        # the priced set judges in the same way.
        measurement_phrase = any(
            any(is_meas for _key, is_meas in dating_list(
                phrase.group(1)))
            for phrase in re.finditer(
                r"\b(?:as (?:measured|counted|tallied|"
                r"totalled|totaled|enumerated|"
                r"inventoried)(?: (?:on|in|"
                r"over|at|during|by|before|after|since|"
                r"from|through|within))?|"
                r"(?:measured|counted|tallied|totalled|"
                r"totaled|enumerated|inventoried) "
                r"(?:on|in|over|at|"
                r"during|by|before|after|since|from|"
                r"through|within)|"
                r"read on|dated|"
                r"as (?:of|at))\s+(%s)" % date_alt,
                sentence.lower()))
        kept = set()
        dropped_figure = False
        kept_figure = False
        for index, (clause, sep, subordinate, _off) in \
                enumerate(clauses):
            if not clause_has_figure(clause):
                kept.add(index)
                continue
            # The exemption test, in the order the
            # docstring states it. First, the clause its
            # own dating, read at every grain with no skip
            # set, a pure date phrase or stamp clause
            # standing directly before the assertion
            # counting as part of that dating.
            own = dating_list(clause)
            own_from_prev = False
            before_clauses = clauses[:index]
            if not own and index:
                prev_clause = clauses[index - 1][0]
                if not clause_has_figure(prev_clause) and \
                        pure_dating_clause(prev_clause):
                    own = dating_list(prev_clause)
                    own_from_prev = True
                    before_clauses = clauses[:index - 1]
            exempt = False
            if own and not any(
                    is_meas for _key, is_meas in own) and \
                    len({key for key, _m in own}) == 1:
                # Second, the clause dating is wholly a
                # dating other than the measurement dating
                # at a single grain, which the condition
                # above holds. Third, no measurement dating
                # and no different dating stands in a
                # governing position before the assertion.
                # The governing before reading takes every
                # dating standing before the clause in the
                # flattened sentence, whatever opener it
                # stands under and whatever separator
                # stands before the clause, so a label
                # fragment glued from the line above is
                # recovered on the from and since openers
                # and on a semicolon as it is on a comma.
                # A subordinate clause carrying its own
                # dating and a clause opening with its own
                # date phrase take their own dating at this
                # step, the earlier dating not governing
                # them.
                if subordinate or initial_dating(clause):
                    exempt = True
                else:
                    # The dating standing before the clause
                    # is read over the earlier clause texts,
                    # whose separators stand outside them, so
                    # a year alone at a clause end is read at
                    # its grain and not lost to its comma.
                    before = dating_list(" ".join(
                        entry[0] for entry in before_clauses))
                    if not any(
                            is_meas
                            for _key, is_meas in before) and \
                            all(key == own[0][0]
                                for key, _m in before):
                        exempt = True
            if measurement_phrase and not subordinate:
                # A measurement phrase in the sentence
                # governs the main assertions of the
                # sentence wherever it stands, before the
                # assertion or after it in a following
                # clause, so an assertion outside a
                # subordinate clause is judged in a
                # measurement phrased sentence even where
                # the test above would exempt it. A
                # subordinate assertion carrying its own
                # dating is governed by that dating and
                # not by the phrase.
                exempt = False
            if not exempt and not own and \
                    not measurement_phrase:
                # The fallback for a clause carrying no
                # dating of its own. The dating of the
                # sentence as a whole governs, mixed dating
                # there including any measurement dating
                # judging and a single other dating
                # exempting.
                whole = dating_list(" ".join(
                    entry[0] for entry in clauses))
                exempt = bool(whole) and not any(
                    is_meas for _key, is_meas in whole) \
                    and len({key for key, _m in whole}) == 1
            if exempt:
                # The sentence level backstop, the fourth
                # step of the docstring passage. A dating
                # standing in a fragment elsewhere in the
                # sentence, a pure dating clause or a date
                # phrase glued at a clause its end, after
                # the assertion its clause as a trailing
                # bare dating fragment or before it with
                # another clause between it and the
                # assertion, defeats the exemption
                # where the dating it carries is a
                # measurement dating at its grain or a
                # dating different from the assertion its
                # own dating, a range counting by both its
                # ends wherever its ends stand. A pure
                # dating clause standing directly before
                # the assertion its clause and supplying
                # its dating is counted in
                # the steps above and stands down here,
                # as a sentence initial preamble does,
                # while one standing after another clause
                # directly before a
                # subordinate clause or a clause opening
                # with its own date phrase is counted
                # nowhere above and is read here, and
                # a dating standing inside a clause of the
                # sentence, a full independent clause
                # carrying its own subject and verb and no
                # figure among them, does not reach the
                # assertion, so no other clause is read
                # here.
                own_keys = {key for key, _m in own}
                if not own_keys:
                    own_keys = {
                        key for key, _m in dating_list(
                            " ".join(
                                entry[0] for entry in clauses))}
                for other_index, (other, _sep2, _sub2,
                                  _off2) in enumerate(clauses):
                    if other_index == index or \
                            (other_index == index - 1
                             and (own_from_prev
                                  or other_index == 0)):
                        continue
                    other_dating = fragment_dating(other)
                    if not other_dating:
                        continue
                    if any(
                            is_meas or key not in own_keys
                            for key, is_meas in other_dating):
                        exempt = False
                        break
            if exempt:
                dropped_figure = True
            else:
                kept_figure = True
                kept.add(index)
        if dropped_figure and not kept_figure:
            carry = None
            carry_largest = None
            carry_grace = False
            continue
        if dropped_figure:
            rebuilt = []
            for index, (clause, sep, subordinate, _off) in \
                    enumerate(clauses):
                if index not in kept:
                    continue
                if rebuilt:
                    rebuilt.append(sep if sep else " ")
                rebuilt.append(clause)
            sentence = "".join(rebuilt)
        tokens, spans = figure_tokens(sentence)
        segments = [
            figure_tokens(segment)
            for segment in segments_of(sentence)]
        covered = canonical_covered(sentence)
        prompt_keys = {
            (seg_span[2], seg_span[3])
            for seg_tokens, seg_spans in segments
            if "prompt" in seg_tokens
            and "description" not in seg_tokens
            and "descriptions" not in seg_tokens
            for seg_span in seg_spans}
        # A priced subject named outright asserts its figure
        # with no superlative anywhere in the sentence. The
        # demo recording is named by any of its names in the
        # packs and the capture record, the demo recording,
        # the hero recording, the demo, the recording, the
        # demo GIF, the gif, the cursor agent demo, the clip
        # and the footage, beside
        # the recording its file name, and the largest plain
        # file is named by its path in full or in part, by
        # its SKILL.md name, or as the skill file or the
        # skill beside a byte size.
        lowered_sentence = sentence.lower()
        demo_named = "demo recording" in lowered_sentence or \
            "hero recording" in lowered_sentence or \
            "cursor agent demo" in lowered_sentence or \
            "recognitio-cursor-agent-demo" in lowered_sentence or \
            DEMO_RECORDING in lowered_sentence or \
            any(word in tokens for word in (
                "demo", "recording", "gif", "capture",
                "video", "walkthrough", "screencast",
                "animation", "movie", "clip", "footage",
                "film", "reel", "trailer", "videotape",
                "showreel", "screencapture", "playback"))
        plain_named = \
            measured["largest_plain_path"].lower() in \
            lowered_sentence or \
            "skill.md" in lowered_sentence or \
            "skill file" in lowered_sentence or \
            "instructions file" in lowered_sentence or \
            ("skill" in tokens and any(
                word in tokens for word in (
                    "bytes", "byte", "kib", "kb", "mib", "mb",
                    "gib", "octet", "octets")))
        has_largest = largest_anchor(tokens) and \
            not ordinal_before(tokens)
        # A subject named under an ordinal, the second
        # largest file, names another quantity and not the
        # priced subject, so the named subject reading
        # stands down for it the way the anchor reading does.
        subject_named = (demo_named or plain_named) and \
            not ordinal_before(tokens)
        # A range states two numbers for one quantity, and
        # the pair is judged as the range it states before
        # either number is read on its own.
        range_ids = set()
        range_keys = set()
        if "between" in tokens:
            after = [
                span for span in spans
                if span[0] > tokens.index("between")]
            if len(after) >= 2:
                low, high = after[0], after[1]
                unit = tokens[high[1] + 1] if \
                    high[1] + 1 < len(tokens) else ""
                ranged = None
                label = None
                low_value, high_value = low[2], high[2]
                if unit == "files":
                    ranged, label = measured["count"], \
                        "tree file count"
                elif unit in hit_nouns:
                    ranged, label = measured["scan_hits"], \
                        "credential scan result"
                elif unit in byte_factors and (
                        has_largest or subject_named):
                    factor = byte_factors[unit]
                    low_value, high_value = \
                        low[2] * factor, high[2] * factor
                    if plain_named and not demo_named:
                        ranged, label = \
                            measured["largest_plain_size"], \
                            "largest plain file"
                    else:
                        ranged, label = \
                            measured["largest_size"], \
                            "largest file"
                elif unit in (
                        "characters", "chars", "glyphs") and (
                        "description" in tokens
                        or "descriptions" in tokens
                        or "summary" in tokens
                        or any(word in tokens for word in (
                            "skill", "reviewer", "agent",
                            "output"))):
                    ranged = desc_target(tokens, high)
                    label = "frontmatter description length"
                if ranged is not None:
                    range_ids = {id(low), id(high)}
                    range_keys = {
                        (low[2], low[3]), (high[2], high[3])}
                    if not low_value <= ranged <= high_value:
                        problems.append(
                            "%s states a %s between %s and %s "
                            "and the tree measures %d"
                            % (CLAUDE_PACK, label, low[3],
                               high[3], ranged))
        asserted = set()
        # The credential scan result, read clause by clause,
        # because a clause that names another tool and its
        # own corpus states that tool its result and not the
        # scan its, while a clause of a scan sentence states
        # the scan result under any of its nouns, results,
        # findings, matches, positives, issues, outcomes or
        # hits, beside the sweep and audit names for the scan.
        for seg_tokens, seg_spans in segments:
            nouns_at = [
                i for i, word in enumerate(seg_tokens)
                if word in hit_nouns]
            if not nouns_at:
                continue
            only_plain_nouns = all(
                seg_tokens[i] in ("hit", "hits")
                for i in nouns_at)
            if not only_plain_nouns and not any(
                    word in seg_tokens for word in (
                        "scan", "credential", "check", "sweep",
                        "audit", "verification", "census",
                        "screening", "inspection", "review",
                        "search", "pattern", "probe",
                        "examination", "survey",
                        "analysis", "inventory", "count",
                        "tally", "listing", "register",
                        "catalogue", "catalog")):
                continue
            if any(word in seg_tokens for word in (
                    "linter", "corpus")) and not any(
                        word in seg_tokens for word in (
                            "scan", "credential")):
                continue
            other_at = [
                i for i, word in enumerate(seg_tokens)
                if word in (
                    "files", "file", "characters", "chars",
                    "glyphs", "bytes", "byte")]
            for span in seg_spans:
                if (span[2], span[3]) in range_keys:
                    continue
                if cap_governed(seg_tokens, span) or \
                        is_year_span(seg_tokens, span):
                    continue
                nearest_noun = min(
                    min(abs(span[0] - at), abs(span[1] - at))
                    for at in nouns_at)
                if other_at:
                    nearest_other = min(
                        min(abs(span[0] - at),
                            abs(span[1] - at))
                        for at in other_at)
                    if nearest_other < nearest_noun:
                        continue
                asserted.add("scan")
                if span[2] in covered["scan"]:
                    continue
                relation = bound_relation(seg_tokens, span)
                if relation is not None:
                    if not bound_holds(
                            relation, span[2],
                            measured["scan_hits"]):
                        problems.append(
                            "%s states a credential scan result "
                            "bound of %s and the scan over this "
                            "tree returns %d"
                            % (CLAUDE_PACK, span[3],
                               measured["scan_hits"]))
                    continue
                unpriced("credential scan result", span[3])
            for at, word in enumerate(seg_tokens):
                if word not in vague_words:
                    continue
                if not any(
                        abs(at - noun) <= 3 for noun in nouns_at):
                    continue
                asserted.add("scan")
                unpriced("credential scan result", word)
        # The scan carryover, consumed the way the other
        # quantities consume theirs. A sentence the carry
        # names, stating a value and naming no quantity of
        # its own in a short sentence or beside a total or
        # count word, is read as the scan result across the
        # pair, and a bare valued sentence of any length
        # carrying a tally marker, the word figure, the
        # word tally, the word altogether, the pair all
        # told, the pair bottom line, the pair came to,
        # the pair came back, the word sum, the verb
        # yielded, the word totalled, the word totaled,
        # the word overall, the pair in all, the
        # triple came out to, the pair stood at, the
        # triple came in at, the triple in the end, the
        # pair added up, the pair ran to, the pair
        # amounted to, the pair closed at, the triple
        # worked out at or the
        # verb found, is read
        # the same way, because a tally
        # sentence states the result of the count it
        # completes at whatever length it runs to.
        if carry == "scan" and "scan" not in asserted:
            carry_named = any(
                word in tokens for word in ("total", "count"))
            carry_pairs = list(zip(tokens, tokens[1:]))
            carry_tally = "figure" in tokens or \
                "found" in tokens or \
                "tally" in tokens or \
                "altogether" in tokens or \
                "sum" in tokens or \
                "yielded" in tokens or \
                "totalled" in tokens or \
                "totaled" in tokens or \
                "overall" in tokens or \
                ("all", "told") in carry_pairs or \
                ("bottom", "line") in carry_pairs or \
                ("came", "to") in carry_pairs or \
                ("came", "back") in carry_pairs or \
                ("in", "all") in carry_pairs or \
                ("stood", "at") in carry_pairs or \
                ("added", "up") in carry_pairs or \
                ("ran", "to") in carry_pairs or \
                ("amounted", "to") in carry_pairs or \
                ("closed", "at") in carry_pairs or \
                any(tokens[i:i + 3] == ["came", "out", "to"]
                    for i in range(len(tokens) - 2)) or \
                any(tokens[i:i + 3] == ["came", "in", "at"]
                    for i in range(len(tokens) - 2)) or \
                any(tokens[i:i + 3] == ["worked", "out", "at"]
                    for i in range(len(tokens) - 2)) or \
                any(tokens[i:i + 3] == ["in", "the", "end"]
                    for i in range(len(tokens) - 2))
            carry_bare = len(spans) == 1 and not any(
                    word in tokens for word in (
                        "files", "file", "bytes", "byte",
                        "characters", "chars", "glyphs",
                        "largest", "biggest", "weightiest",
                        "description", "descriptions"))
            carry_short = carry_bare and len(tokens) <= 8
            if carry_named or carry_short or \
                    (carry_bare and carry_tally):
                for span in spans:
                    if cap_governed(tokens, span) or \
                            is_year_span(tokens, span):
                        continue
                    asserted.add("scan")
                    unpriced(
                        "credential scan result", span[3])
        # The remaining priced quantities, read span by span
        # over the whole sentence.
        for span in spans:
            if id(span) in range_ids or \
                    is_year_span(tokens, span):
                continue
            if cap_governed(tokens, span):
                # A cap governed figure is a checklist limit
                # rather than a measurement, except that the
                # file count cap is itself a stated fact of
                # the pack, so a file count stated as a cap
                # outside the canonical capped statement is
                # judged against the cap the pack states.
                cap_unit = tokens[span[1] + 1] if \
                    span[1] + 1 < len(tokens) else ""
                if cap_unit == "files" and \
                        span[2] not in covered["count"] and \
                        span[2] != 512:
                    problems.append(
                        "%s states a tree file count cap of "
                        "%s files and the checklist cap the "
                        "pack states is 512 files"
                        % (CLAUDE_PACK, span[3]))
                continue
            if span[0] > 0 and \
                    tokens[span[0] - 1] == "version":
                continue
            unit = tokens[span[1] + 1] if \
                span[1] + 1 < len(tokens) else ""
            if unit in hit_nouns:
                continue
            if unit in multipliers and \
                    span[1] + 2 < len(tokens) and tokens[
                        span[1] + 2] in (
                            "characters", "chars", "glyphs",
                            "files", "bytes", "byte"):
                span = (
                    span[0], span[1],
                    span[2] * multipliers[unit], span[3])
                unit = tokens[span[1] + 2]
            quantity = None
            target = None
            label = None
            converted = span[2]
            if unit in ("characters", "chars", "glyphs") and (
                    span[2], span[3]) in prompt_keys:
                continue
            if unit in ("characters", "chars", "glyphs") and (
                    "description" in tokens
                    or "descriptions" in tokens
                    or "summary" in tokens
                    or carry == "desc"
                    or any(word in tokens for word in (
                        "skill", "reviewer", "agent",
                        "output"))):
                quantity, label = "desc", \
                    "frontmatter description length"
                target = desc_target(tokens, span)
            elif unit in byte_factors and (
                    has_largest or carry == "largest"
                    or subject_named):
                quantity = "largest"
                if plain_named and not demo_named and \
                        not has_largest:
                    _path, target, label = (
                        measured["largest_plain_path"],
                        measured["largest_plain_size"],
                        "largest plain file")
                elif has_largest:
                    _path, target, label = largest_target(tokens)
                elif demo_named:
                    _path, target, label = (
                        measured["largest_path"],
                        measured["largest_size"],
                        "largest file")
                else:
                    _path, target, label = carry_largest
                converted = span[2] * byte_factors[unit]
            elif unit == "file" and span[1] + 2 < len(tokens) \
                    and tokens[span[1] + 2] in (
                        "entries", "total", "count"):
                quantity, label = "count", "tree file count"
                target = measured["count"]
            elif unit in (
                    "files", "entries", "items", "paths"):
                if unit == "files" or any(
                        word in tokens for word in (
                            "repo", "repository", "tree",
                            "scan", "bundle", "package",
                            "archive")):
                    quantity, label = "count", \
                        "tree file count"
                    target = measured["count"]
            if quantity is None:
                # A value with no unit word of its own still
                # asserts a priced quantity where the words
                # around it name one, a files noun ahead of it
                # with no competing unit between, a file count
                # phrase, a count verb over the repo or the
                # tree, or the quantity the sentence before it
                # named and left unvalued.
                if unit in competing_units:
                    continue
                if any(word in competing_units for word in
                        tokens[span[1] + 1:span[1] + 4]):
                    continue
                if span[0] > 0 and tokens[span[0] - 1] in (
                        "entries", "items") and (
                        len(tokens) <= 5
                        or "| entries" in lowered_sentence
                        or "| items" in lowered_sentence
                        or any(
                            word in tokens for word in (
                                "repo", "repository", "tree",
                                "scan", "bundle", "package",
                                "archive"))):
                    # A label form, a table row or a label
                    # line naming its count noun before its
                    # value, asserts the count under that
                    # noun with no unit after the value.
                    quantity, label = "count", \
                        "tree file count"
                    target = measured["count"]
                after_files = [
                    i for i in range(span[1] + 1, len(tokens))
                    if tokens[i] == "files"]
                if after_files and span[1] + 1 < len(tokens) \
                        and tokens[span[1] + 1] == "of" \
                        and not any(
                        word in competing_units
                        for word in tokens[
                            span[1] + 1:after_files[0]]):
                    quantity, label = "count", \
                        "tree file count"
                    target = measured["count"]
                if quantity is None and any(
                        tokens[i:i + 2] in (
                            ["file", "count"], ["file", "total"])
                        for i in range(len(tokens) - 1)):
                    quantity, label = "count", \
                        "tree file count"
                    target = measured["count"]
                if quantity is None and any(
                        abs(span[0] - at) <= 4
                        for at, word in enumerate(tokens)
                        if word == "count"):
                    quantity, label = "count", \
                        "tree file count"
                    target = measured["count"]
                if quantity is None:
                    for at in range(span[0] - 1, -1, -1):
                        word = tokens[at]
                        if word == "files":
                            pass
                        elif word == "file" and \
                                at + 1 < len(tokens) and \
                                tokens[at + 1] in (
                                    "count", "total",
                                    "entries"):
                            pass
                        elif word == "count" and (
                                "file" in tokens
                                or "files" in tokens
                                or carry == "count"):
                            pass
                        else:
                            continue
                        between = tokens[at + 1:span[0]]
                        if all(
                                word in linking_words
                                for word in between):
                            quantity, label = "count", \
                                "tree file count"
                            target = measured["count"]
                        break
                if quantity is None and any(
                        word in tokens for word in (
                            "repo", "repository", "tree")) and \
                        any(word in count_verbs
                            for word in tokens):
                    quantity, label = "count", \
                        "tree file count"
                    target = measured["count"]
                # The count carryover consumes a bare
                # valued sentence of any length carrying a
                # tally marker beside its short form, the
                # same tally set the scan carryover holds,
                # the word figure, the word tally, the word
                # altogether, the pair all told, the pair
                # bottom line, the pair came to, the pair
                # came back, the word sum, the verb yielded,
                # the word totalled, the word totaled, the
                # word overall, the pair in all, the
                # triple came out to, the pair stood at,
                # the triple came in at, the triple in the
                # end, the pair added up, the pair ran to,
                # the pair amounted to, the pair closed at,
                # the triple worked out
                # at and the verb found. The lane 7 commit body stated
                # this consumption for both carryovers
                # while this condition held only the word
                # figure and the pair came to, so the
                # correction stands here in the code, the
                # body itself standing unedited on the
                # record.
                if quantity is None and carry == "count" and \
                        len(spans) == 1 \
                        and not any(
                            word in tokens for word in (
                                "files", "file", "hits", "hit",
                                "bytes", "byte", "characters",
                                "chars", "glyphs", "largest",
                                "biggest", "count", "description",
                                "descriptions")) \
                        and (len(tokens) <= 8 or "figure" in tokens
                             or "found" in tokens
                             or "tally" in tokens
                             or "altogether" in tokens
                             or ("all", "told") in list(zip(
                                 tokens, tokens[1:]))
                             or ("bottom", "line") in list(zip(
                                 tokens, tokens[1:]))
                             or ("came", "to") in list(zip(
                                 tokens, tokens[1:]))
                             or ("came", "back") in list(zip(
                                 tokens, tokens[1:]))
                             or "sum" in tokens
                             or "yielded" in tokens
                             or "totalled" in tokens
                             or "totaled" in tokens
                             or "overall" in tokens
                             or ("in", "all") in list(zip(
                                 tokens, tokens[1:]))
                             or ("stood", "at") in list(zip(
                                 tokens, tokens[1:]))
                             or ("added", "up") in list(zip(
                                 tokens, tokens[1:]))
                             or ("ran", "to") in list(zip(
                                 tokens, tokens[1:]))
                             or ("amounted", "to") in list(zip(
                                 tokens, tokens[1:]))
                             or ("closed", "at") in list(zip(
                                 tokens, tokens[1:]))
                             or any(
                                 tokens[i:i + 3] == [
                                     "came", "out", "to"]
                                 for i in range(
                                     len(tokens) - 2))
                             or any(
                                 tokens[i:i + 3] == [
                                     "came", "in", "at"]
                                 for i in range(
                                     len(tokens) - 2))
                             or any(
                                 tokens[i:i + 3] == [
                                     "worked", "out", "at"]
                                 for i in range(
                                     len(tokens) - 2))
                             or any(
                                 tokens[i:i + 3] == [
                                     "in", "the", "end"]
                                 for i in range(
                                     len(tokens) - 2))):
                    quantity, label = "count", \
                        "tree file count"
                    target = measured["count"]
                if quantity is None and carry == "count" and \
                        any(word in tokens for word in (
                            "count", "total")):
                    quantity, label = "count", \
                        "tree file count"
                    target = measured["count"]
            if quantity is None:
                continue
            asserted.add(quantity)
            cover_key = quantity
            if quantity == "largest":
                cover_key = "plain" if label == \
                    "largest plain file" else "largest"
            if converted in covered.get(cover_key, set()):
                continue
            relation = bound_relation(tokens, span)
            if relation is not None:
                if target is not None and not bound_holds(
                        relation, converted, target):
                    problems.append(
                        "%s states a %s bound of %s and the "
                        "tree measures %d"
                        % (CLAUDE_PACK, label, span[3], target))
                continue
            unpriced(label, span[3])
        # Vague magnitude words state a value with no numeral
        # at all, and they assert the quantity their anchor
        # names in the same way.
        spelled_indices = {
            i for span in spans
            for i in range(span[0], span[1] + 1)}
        for at, word in enumerate(tokens):
            if word not in vague_words or at in spelled_indices:
                continue
            following = tokens[at + 1:at + 4]
            stripped = [
                item for item in following if item != "of"]
            if not stripped:
                continue
            head = stripped[0]
            if head == "files":
                unpriced("tree file count", word)
                asserted.add("count")
            elif head in ("characters", "chars", "glyphs") and (
                    "description" in tokens
                    or "descriptions" in tokens):
                unpriced(
                    "frontmatter description length", word)
                asserted.add("desc")
            elif head in byte_factors and (
                    has_largest or subject_named):
                if has_largest:
                    _path, _target, label = largest_target(tokens)
                elif plain_named and not demo_named:
                    label = "largest plain file"
                else:
                    label = "largest file"
                unpriced(label, word)
                asserted.add("largest")
        # A fraction of a unit states a determinate value
        # with no numeral and no spelled number, half a MiB
        # or three quarters of a MiB, and inside a sentence
        # anchored on a priced size it asserts that size in
        # the same way. The fraction forms are the spelled
        # forms with denominators to tenths, in their plain
        # and hyphenated spellings, the bare half and
        # quarter forms, and the digit forms with
        # denominators to tenths, so the digit reading
        # holds the same declared boundary as the spelled
        # one, denominators past tenths stating no fraction
        # the gate reads in either form. A percent of a
        # unit and a decimal standing before of a unit are
        # the proportional forms of the same family and are
        # read beside them, the percent in digits or
        # spelled out or as per cent or per-cent, or as
        # pct, per mille or per thousand, a
        # percent sign after a spelled number counting
        # in the spelled register, a percent stated
        # against the size of a unit counting in the
        # same way as one stated of the unit, a decimal
        # stated against the size of a unit counting in
        # the same way, the decimal with a
        # leading point where it carries no digit before
        # it, and the article before the unit a, an or the
        # in every proportional form.
        fraction_match = re.search(
            r"\b(?:[0-9]+/(?:[1-9]|10)\b"
            r"|(?:a|an|one|two|three|four|five|six|seven|"
            r"eight|nine|ten|eleven)[ -]"
            r"(?:half|halves|quarter|quarters|third|thirds|"
            r"fourth|fourths|fifth|fifths|sixth|sixths|"
            r"seventh|sevenths|eighth|eighths|ninth|ninths|"
            r"tenth|tenths)"
            r"|a half|half|quarter)"
            r"\s+(?:of\s+)?(?:(?:a|an|the)\s+)?"
            r"(bytes?|kib|kb|mib|mb|gib|b|octets?)"
            r"\b", lowered_sentence)
        percent_match = re.search(
            r"\b[0-9]+(?:\.[0-9]+)?\s*(?:%|percent|pct|"
            r"per[-\s]+cent|per\s+mille|per\s+thousand)"
            r"\s+(?:of|the\s+size\s+of)\s+(?:a|an|the)\s+"
            r"(bytes?|kib|kb|mib|mb|gib|b|octets?)\b",
            lowered_sentence)
        if percent_match is None:
            # A percent stated in the spelled register, the
            # register the gate reads everywhere else, is a
            # proportion in the same way. The words standing
            # before the percent word are read back over the
            # spelled number words, and the shape counts
            # where a spelled number stands there.
            spelled_number_words = set(NUMBER_UNITS) | \
                set(NUMBER_TENS) | {
                    "hundred", "thousand", "and", "a", "an"}
            for cand in re.finditer(
                    r"(?:percent|pct|per[-\s]+cent|%)\s+"
                    r"(?:of|the\s+size\s+of)\s+"
                    r"(?:a|an|the)\s+"
                    r"(bytes?|kib|kb|mib|mb|gib|b|octets?)\b",
                    lowered_sentence):
                before_words = re.findall(
                    r"[a-z]+", lowered_sentence[:cand.start()])
                run = []
                for word in reversed(before_words):
                    if word in spelled_number_words:
                        run.append(word)
                    else:
                        break
                if run and any(
                        word in NUMBER_UNITS
                        or word in NUMBER_TENS
                        for word in run):
                    percent_match = cand
                    break
        decimal_of_match = re.search(
            r"(?:^|\s)(?:[0-9]+\.[0-9]+|\.[0-9]+)"
            r"\s+of\s+(?:a|an|the)\s+"
            r"(bytes?|kib|kb|mib|mb|gib|b|octets?)\b",
            lowered_sentence)
        decimal_size_match = re.search(
            r"(?:^|\s)(?:[0-9]+\.[0-9]+|\.[0-9]+)"
            r"\s+the\s+size\s+of\s+(?:a|an|the)\s+"
            r"(bytes?|kib|kb|mib|mb|gib|b|octets?)\b",
            lowered_sentence)
        if percent_match or decimal_of_match or \
                decimal_size_match:
            fraction_match = percent_match or \
                decimal_of_match or decimal_size_match
        if fraction_match and (
                has_largest or subject_named
                or carry == "largest"):
            if plain_named and not demo_named and \
                    not has_largest:
                fraction_label = "largest plain file"
            elif has_largest:
                _path, _target, fraction_label = \
                    largest_target(tokens)
            else:
                fraction_label = "largest file"
            unpriced(fraction_label, fraction_match.group(0))
            asserted.add("largest")
        # The carryover for the next sentence, which stands
        # only when this sentence named a quantity and stated
        # no value for it. One intervening sentence that
        # states no value and asserts no priced quantity of
        # its own does not discharge the carry, so a valued
        # sentence standing two sentences on is still read
        # across the split. A second intervening sentence,
        # or any sentence that states a value or asserts a
        # quantity, discharges it.
        new_carry = None
        new_carry_largest = None
        if has_largest and "largest" not in asserted:
            new_carry = "largest"
            new_carry_largest = largest_target(tokens)
        elif ("description" in tokens
                or "descriptions" in tokens) \
                and "desc" not in asserted:
            new_carry = "desc"
        elif any(word in tokens for word in (
                "scan", "credential")) and any(
                    word in tokens for word in hit_nouns) \
                and "scan" not in asserted:
            new_carry = "scan"
        elif ("files" in tokens
                or "file" in tokens
                or any(
                    tokens[i:i + 2] in (
                        ["file", "count"], ["file", "total"])
                    for i in range(len(tokens) - 1))) \
                and "count" not in asserted:
            new_carry = "count"
        elif "scan" in tokens and "count" not in asserted:
            new_carry = "count"
        elif any(word in tokens for word in (
                "counted", "census")) \
                and "count" not in asserted:
            # A counted or census sentence names the file
            # count quantity in its verb or its noun, so a
            # bare value in the next sentence is read across
            # the pair the way the other carryovers are.
            new_carry = "count"
        if new_carry is not None:
            carry = new_carry
            carry_largest = new_carry_largest
            carry_grace = False
        elif carry is not None and not carry_grace \
                and not asserted and not any(
                    not is_year_span(tokens, span)
                    for span in spans) and not any(
                    word in vague_words for word in tokens):
            # A sentence carrying a year span alone, a
            # dated run note, states no value and asserts
            # no priced quantity, so it stands as an
            # intervening sentence here in the same way
            # as a sentence carrying no span at all.
            carry_grace = True
        else:
            carry = None
            carry_largest = None
            carry_grace = False


def shipped_path(root, value):
    """Resolve a manifest path, refusing the forbidden shapes.

    An absolute value, a parent reference, and an empty value
    resolve to nothing here rather than being normalised into
    the tree, because both platforms forbid those shapes and
    a gate that rewrites them before judging them cannot
    fail for the reason it exists.
    """
    if not isinstance(value, str) or not value:
        return None
    if value.startswith("/") or value.startswith("\\"):
        return None
    parts = value.split("/")
    if ".." in parts:
        return None
    if value.startswith("./"):
        value = value[2:]
    return root / value


def pack_problems(root, version, problems):
    for rel, routes in PACK_ROUTES.items():
        path = root / rel
        if path.exists() and not path.is_file():
            problems.append(
                "%s cannot be read, it is not a regular file" % rel)
            continue
        try:
            raw = path.read_text(encoding="utf-8")
        except OSError:
            problems.append("%s is missing" % rel)
            continue
        # The packs wrap their prose across lines, so the
        # pinned sentences are read on the flattened text.
        text = re.sub(r"\s+", " ", raw)
        for fragment in COMMON_FRAGMENTS:
            if fragment not in text:
                problems.append(
                    "%s no longer states %r" % (rel, fragment))
        if version is not None:
            sentence = "written against version %s of recognitio" % version
            if sentence not in text:
                problems.append(
                    "%s no longer states the version sentence for "
                    "%s" % (rel, version))
        for route in routes:
            if route not in text:
                problems.append(
                    "%s no longer names %r" % (rel, route))
        for pin in PACK_PINS[rel]:
            if pin not in text:
                problems.append(
                    "%s no longer states %r" % (rel, pin))
        lowered = text.lower().replace(HONEST_SENTENCE, "")
        claims = BANNED_CLAIMS + PACK_BANNED_CLAIMS.get(rel, ())
        for claim in claims:
            if claim in lowered:
                problems.append(
                    "%s carries the filed listing claim %r and "
                    "nothing in the pack has been submitted"
                    % (rel, claim))
        if TIMELINE_CLAIM.search(lowered):
            problems.append(
                "%s promises a review timeline and no primary "
                "source states one" % rel)


def cursor_problems(root, problems):
    plugin = load_manifest(root, CURSOR_PLUGIN, problems)
    market = load_manifest(root, CURSOR_MARKET, problems)
    if plugin is not None:
        field_problems(
            CURSOR_PLUGIN, plugin, "description", problems,
            "and the submission checklist asks for one that "
            "states the purpose")
        if not author_name(plugin):
            problems.append(
                "%s carries no author name" % CURSOR_PLUGIN)
        license_problems(CURSOR_PLUGIN, plugin, problems)
        logo = shipped_path(root, plugin.get("logo"))
        if logo is None or not logo.is_file():
            problems.append(
                "%s names a logo path that does not resolve in "
                "the tree" % CURSOR_PLUGIN)
        # Every path in the Cursor manifest resolves from
        # the one plugin root, which is the repo root in
        # this tree, as the Cursor gate reads them. A path
        # written from the manifest folder resolves nowhere
        # under that base.
        for value in plugin.get("skills") or []:
            target = shipped_path(root, value)
            if target is None or not (target / "SKILL.md").is_file():
                problems.append(
                    "%s names a skills path with no SKILL.md "
                    "inside it" % CURSOR_PLUGIN)
        for value in plugin.get("rules") or []:
            target = shipped_path(root, value)
            if target is None or not target.is_file():
                problems.append(
                    "%s names a rule path that does not resolve "
                    "in the tree" % CURSOR_PLUGIN)
    if market is not None:
        field_problems(
            CURSOR_MARKET, market, "name", problems,
            "and the reference marks it required")
        owner_problems(
            CURSOR_MARKET, market, problems,
            "and the reference marks it required")
        entry_problems(CURSOR_MARKET, market, plugin, problems)


def claude_problems(root, problems):
    plugin = load_manifest(root, CLAUDE_PLUGIN, problems)
    market = load_manifest(root, CLAUDE_MARKET, problems)
    version = None
    if plugin is not None:
        version = plugin.get("version")
        if not version:
            problems.append(
                "%s carries no version and the packs state the "
                "version they were written against" % CLAUDE_PLUGIN)
        for field in ("displayName", "description", "keywords",
                      "homepage"):
            field_problems(
                CLAUDE_PLUGIN, plugin, field, problems,
                "and the pack evidence check names it as carried")
        if plugin.get("repository") != REPO_URL:
            problems.append(
                "%s carries repository %r and the pack states "
                "the public repo"
                % (CLAUDE_PLUGIN, plugin.get("repository")))
        if not author_name(plugin):
            problems.append(
                "%s carries no author name and the directory "
                "checklist warns on its absence" % CLAUDE_PLUGIN)
        license_problems(CLAUDE_PLUGIN, plugin, problems)
        icon = shipped_path(root, plugin.get("icon"))
        if icon is None or not icon.is_file():
            problems.append(
                "%s names an icon path that does not resolve "
                "in the tree" % CLAUDE_PLUGIN)
        for value in plugin.get("skills") or []:
            target = shipped_path(root, value)
            if target is None or not target.is_dir():
                problems.append(
                    "%s names a skills path that does not "
                    "resolve inside the folder" % CLAUDE_PLUGIN)
        for field in ("agents", "outputStyles"):
            for value in plugin.get(field) or []:
                target = shipped_path(root, value)
                if target is None or not target.is_file():
                    problems.append(
                        "%s names a %s path that does not "
                        "resolve inside the folder"
                        % (CLAUDE_PLUGIN, field))
    if market is not None:
        field_problems(
            CLAUDE_MARKET, market, "name", problems,
            "and the marketplace reference marks it required")
        owner_problems(
            CLAUDE_MARKET, market, problems,
            "and the marketplace reference marks it required")
        entry = claude_entry_problems(
            CLAUDE_MARKET, market, plugin, problems)
        if entry is not None:
            if entry.get("source") != "./":
                problems.append(
                    "%s entry carries source %r and the pack "
                    "states the root"
                    % (CLAUDE_MARKET, entry.get("source")))
            if entry.get("strict") is not True:
                problems.append(
                    "%s entry carries strict %r and the pack "
                    "states strict mode on"
                    % (CLAUDE_MARKET, entry.get("strict")))
    if not (root / "LICENSE").is_file():
        problems.append(
            "LICENSE is missing from the plugin folder the "
            "Claude pack names")
    return version


def portable_problems(root, problems):
    data = load_manifest(root, PORTABLE, problems)
    if data is None:
        return
    extra = sorted(set(data) - CLOSED_FIELDS)
    if extra:
        problems.append(
            "%s carries top level fields outside the closed "
            "set of the specification, %s"
            % (PORTABLE, ", ".join(extra)))
    if data.get("$schema") != SCHEMA_URL:
        problems.append(
            "%s carries $schema %r and the pack states the "
            "canonical 1.0.0 schema"
            % (PORTABLE, data.get("$schema")))
    name = data.get("name")
    if name != "recognitio":
        problems.append(
            "%s carries name %r and the pack states the "
            "shipped package name" % (PORTABLE, name))
    if not isinstance(name, str) \
            or not NAME_PATTERN.fullmatch(name) \
            or "--" in name or ".." in name or len(name) > 64:
        problems.append(
            "%s carries name %r outside the pattern the "
            "specification names" % (PORTABLE, name))
    if not semver_ok(data.get("version")):
        problems.append(
            "%s carries version %r and the host listing asks "
            "for a semantic version" % (PORTABLE, data.get("version")))
    field_problems(
        PORTABLE, data, "description", problems,
        "and the host listing asks for one")
    if not author_name(data):
        problems.append(
            "%s carries no author name and the host listing "
            "asks for one" % PORTABLE)
    license_problems(PORTABLE, data, problems)
    if data.get("homepage") != REPO_URL:
        problems.append(
            "%s carries homepage %r and the pack states the "
            "public repo" % (PORTABLE, data.get("homepage")))
    if data.get("repository") != REPO_URL:
        problems.append(
            "%s carries repository %r and the host listing "
            "files against the public repo"
            % (PORTABLE, data.get("repository")))
    expected_keywords = ["agent-skills", "code-review",
                         "diff", "git", "pull-request",
                         "review-packet"]
    if data.get("keywords") != expected_keywords:
        problems.append(
            "%s carries keywords %r and the pack states the "
            "set the host listing would read"
            % (PORTABLE, data.get("keywords")))
    keywords = data.get("keywords")
    if isinstance(keywords, list):
        for word in keywords:
            if not isinstance(word, str) \
                    or not KEYWORD_PATTERN.fullmatch(word):
                problems.append(
                    "%s carries keyword %r outside the lowercase "
                    "hyphenated form the host listing asks for"
                    % (PORTABLE, word))
    extensions = data.get("extensions")
    if not isinstance(extensions, dict) or not extensions:
        problems.append(
            "%s carries no extension declarations and the "
            "package exists to carry them" % PORTABLE)
    skill = root / "agent-plugins-package" / "skills" \
        / "recognitio" / "SKILL.md"
    if not skill.is_file():
        problems.append(
            "the portable package skill is missing from its "
            "fixed location")


def cursor_pack_figure_problems(root, problems):
    """Check the Cursor pack tree figures against the tree.

    Round 16. The figure family read the Claude pack
    alone, so a tree figure stated in the Cursor pack
    stood unjudged and a stale count planted in its
    summary passed the gate. The Cursor pack states
    no tree figure today. Any file count statement it
    carries in the holds form the family prices, a
    repo, repository or tree holds form, is judged
    against the measured tree, so such a statement
    refuses by name when its figure drifts.
    """
    path = root / CURSOR_PACK
    try:
        raw = path.read_text(encoding="utf-8")
    except OSError:
        return
    measured = tree_measurements(root)
    if measured is None:
        return
    text = re.sub(r"\s+", " ", raw)
    number = r"([0-9][0-9,]*)"
    for holds in re.finditer(
        r"\b(?:the )?(?:repo|repository|tree) holds %s files"
        % number, text, re.IGNORECASE
    ):
        claimed = int(holds.group(1).replace(",", ""))
        if claimed != measured["count"]:
            problems.append(
                "%s states the tree holds %s files and the "
                "tree holds %d"
                % (CURSOR_PACK, holds.group(1),
                   measured["count"]))


def submissions_problems(root=None):
    """Problems with the submission packs or their facts."""
    root = ROOT if root is None else root
    problems = []
    cursor_problems(root, problems)
    version = claude_problems(root, problems)
    portable_problems(root, problems)
    pack_problems(root, version, problems)
    figure_problems(root, problems)
    cursor_pack_figure_problems(root, problems)
    return problems


def main():
    problems = submissions_problems()
    if problems:
        for problem in problems:
            print("check_submissions: %s" % problem, file=sys.stderr)
        return 1
    print(
        "check_submissions: the three submission packs state "
        "in their own text that nothing in them has been "
        "submitted and state the shipped version, and every "
        "manifest fact their evidence checks rest on holds "
        "in the tree"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
