#!/usr/bin/env python3
"""Pin the Build 19 Codex plugin build.

Build 19 carries recognitio into Codex on three surfaces the
primary OpenAI documentation names. The canonical skill
already stands in the .agents/skills location Codex scans, so
the build adds the Codex specific file agents/openai.yaml
inside the skill folder, the com.openai extension object in
the portable manifest at agent-plugins-package/plugin.json,
and the repo marketplace at .agents/plugins/marketplace.json
that offers the package. This script pins that arrangement
without a Codex host. The extension object must hold exactly
one interface object with the pinned discovery values, because
the primary packaging page makes the extension the source of
OpenAI specific settings and lets it replace the compatibility
overlay whole, so a .codex-plugin directory beside it would be
dead configuration. The interface logo paths must resolve to
the one icon in the package assets, byte identical to the
brand master, so the package cannot drift from the brand
record. The marketplace must offer the single recognitio
plugin with its source at the portable package and the policy
and category fields the primary page requires on every entry.
The openai.yaml copies must stay byte identical across the
skill spellings, with implicit invocation left on and no tool
dependencies declared, because the workflow needs no MCP
tool. The brief at docs/codex-plugin-brief.md must state the
probe result and the unverified remainder, every rule in it
must carry a derivation note naming a canonical skill section
or a primary OpenAI citation, and a contradicting sentence
appended to the brief must fail on the listing and verified
negatives the build's honesty rests on. Decision 29 must
record the build with its decision 4 statement.
"""

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

NAMESPACE = "com.openai"
CANONICAL_SENTENCE = (
    "Pulls the relevant changes from a pull request or a commit "
    "range, with the context a reviewer needs, into one verified "
    "review packet."
)
LONG_DESCRIPTION = (
    "Recognitio pulls the relevant changes from a pull request or a "
    "commit range out of the local clone, with the context a reviewer "
    "needs, and assembles them into one review packet across four "
    "tiers. A manifest records every changed file and hunk, and an "
    "independent recount must agree with the manifest before the "
    "packet is called verified. A packet whose verified flag is false "
    "is never reviewed as if it were whole."
)
DISPLAY_NAME = "Recognitio"
DEVELOPER_NAME = "David Engelmann"
CATEGORY = "Productivity"
CAPABILITIES = ["Read", "Write"]
DEFAULT_PROMPT = [
    "Use recognitio to build a verified review packet for this change."
]
ICON_PATH = "./assets/icon-512.png"
INTERFACE_FIELDS = {
    "brandColor",
    "capabilities",
    "category",
    "composerIcon",
    "defaultPrompt",
    "developerName",
    "displayName",
    "logo",
    "longDescription",
    "shortDescription",
    "websiteURL",
}
SHORT_DESCRIPTION = (
    "Builds one verified review packet from a pull request or a "
    "commit range in the local clone"
)
SKILL_DEFAULT_PROMPT = (
    "Use recognitio to build a verified review packet for this change"
)
SKILL_TREES = (
    ".agents/skills/recognitio",
    "agent-plugins-package/skills/recognitio",
    ".cursor-plugin/skills/recognitio",
)

BRIEF_SENTENCES = (
    (
        "the changelog skill announcement",
        "The Codex changelog entry dated 2025-12-19 announces agent "
        "skills in Codex",
    ),
    (
        "the skill scan location",
        "Codex scans `.agents/skills` in every directory from the "
        "working directory up to the repository root",
    ),
    (
        "the overlay replacement rule",
        "it replaces the entire `.codex-plugin/plugin.json` overlay",
    ),
    (
        "the extension restraint",
        "so the extension declares neither an apps mapping nor hooks",
    ),
    (
        "the no listing honesty sentence",
        "No universal plugin directory listing exists or has been "
        "submitted for recognitio",
    ),
    (
        "the CLI probe result",
        "registered the repo marketplace and listed "
        "recognitio@recognitio with its source at the portable package",
    ),
    (
        "the unverified remainder",
        "Invocation inside a live Codex session stays unverified",
    ),
    (
        "the CLI probe version",
        "the Codex CLI on this box, version 0.164.0-alpha.9",
    ),
    (
        "the probe scratch home",
        "The probe ran with a scratch Codex home",
    ),
    (
        "the CLI probe install result",
        "installed recognitio@recognitio into the scratch home cache",
    ),
    (
        "the CLI probe install path",
        "plugins/cache/recognitio/recognitio/1.3.0",
    ),
    (
        "the CLI probe installed state",
        "showed it installed and enabled",
    ),
)

RULES_HEADING = "## The Codex plugin rules"

# Claim stems that contradict the build's honesty sentences on
# any surface that carries them. The honest forms never contain
# these stems, because each honest sentence negates or scopes
# the claim it makes, so a stem standing anywhere on the
# surface is a contradiction and not a restatement.
CONTRADICTION_STEMS = (
    "invoked inside a live Codex session",
    "desktop app stands verified",
    "universal plugin directory listing has been submitted",
    "a universal plugin directory listing exists for recognitio",
)
README_INSTALL_SENTENCE = (
    "install recognitio from that marketplace in the Plugins "
    "Directory of the ChatGPT desktop app"
)
README_STALE = "and install the recognitio plugin it offers"

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

# Primary citations a derivation note may name, written as URL
# stems so the note pins the surface the claim was read from.
PRIMARY_CITATIONS = (
    "developers.openai.com/codex/skills",
    "developers.openai.com/plugins/build/plugins",
    "learn.chatgpt.com/docs/changelog",
    "docs/brand/palette.json",
    "scripts/check_brand.py",
)


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


def load_json(root, rel, problems, label):
    """Parse one strict JSON file, recording any problem."""
    path = root / rel
    if path.exists() and not path.is_file():
        problems.append(
            "the %s at %s cannot be read, "
            "it is not a regular file" % (label, rel))
        return None
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        problems.append("the %s at %s is missing" % (label, rel))
        return None
    try:
        data = strict_json_loads(text)
    except (json.JSONDecodeError, DuplicateKeyError) as exc:
        problems.append("the %s does not parse, %s" % (label, exc))
        return None
    if not isinstance(data, dict):
        problems.append("the %s is not a JSON object" % label)
        return None
    return data


def palette_accent(root, problems):
    """The accent colour the brand palette record carries."""
    data = load_json(root, "docs/brand/palette.json", problems,
                     "brand palette record")
    if data is None:
        return None
    accent = data.get("accent")
    if not isinstance(accent, str):
        problems.append("the brand palette record carries no accent")
        return None
    return accent


def extension_problems(manifest, accent, problems):
    """Problems with the com.openai extension in the manifest."""
    extensions = manifest.get("extensions")
    if not isinstance(extensions, dict):
        problems.append(
            "the portable manifest carries no extensions object, so "
            "the com.openai namespace has nowhere to stand"
        )
        return
    namespace = extensions.get(NAMESPACE)
    if not isinstance(namespace, dict):
        problems.append(
            "the portable manifest names no %r namespace, so Codex "
            "gets no OpenAI specific settings" % NAMESPACE
        )
        return
    if set(namespace) != {"interface"}:
        problems.append(
            "the com.openai extension holds %r, not the single "
            "interface object, so it declares an apps mapping, hooks, "
            "or another surface recognitio does not ship"
            % sorted(namespace)
        )
        return
    interface = namespace["interface"]
    if not isinstance(interface, dict):
        problems.append("the com.openai interface is not an object")
        return
    if set(interface) != INTERFACE_FIELDS:
        problems.append(
            "the com.openai interface fields are %r, not the pinned "
            "discovery field set" % sorted(interface)
        )
    expected = {
        "displayName": DISPLAY_NAME,
        "shortDescription": CANONICAL_SENTENCE,
        "longDescription": LONG_DESCRIPTION,
        "developerName": DEVELOPER_NAME,
        "category": CATEGORY,
        "capabilities": CAPABILITIES,
        "websiteURL": manifest.get("repository"),
        "defaultPrompt": DEFAULT_PROMPT,
        "logo": ICON_PATH,
        "composerIcon": ICON_PATH,
    }
    for field, value in sorted(expected.items()):
        if interface.get(field) != value:
            problems.append(
                "the com.openai interface %s is %r, not the pinned "
                "value %r" % (field, interface.get(field), value)
            )
    if accent is not None and interface.get("brandColor") != accent:
        problems.append(
            "the com.openai interface brandColor is %r, not the "
            "palette accent %r" % (interface.get("brandColor"), accent)
        )


def asset_problems(root, problems):
    """Problems with the package assets the interface names."""
    package = root / "agent-plugins-package"
    assets = package / "assets"
    if not assets.is_dir():
        problems.append(
            "agent-plugins-package/assets is missing, so the "
            "interface logo paths resolve nowhere"
        )
        return
    names = sorted(
        str(path.relative_to(assets))
        for path in assets.rglob("*")
        if "__pycache__" not in path.parts
    )
    if names != ["icon-512.png"]:
        problems.append(
            "agent-plugins-package/assets holds %r, not the single "
            "icon-512.png the interface names" % (names,)
        )
        return
    brand = root / "docs" / "brand" / "recognitio-icon-512.png"
    if brand.exists() and not brand.is_file():
        problems.append(
            "the brand icon master cannot be read, "
            "it is not a regular file")
        return
    try:
        brand_bytes = brand.read_bytes()
    except OSError:
        problems.append("the brand icon master is missing")
        return
    icon = assets / "icon-512.png"
    if not icon.is_file():
        problems.append(
            "agent-plugins-package/assets/icon-512.png cannot "
            "be read, it is not a regular file"
        )
    elif icon.read_bytes() != brand_bytes:
        problems.append(
            "agent-plugins-package/assets/icon-512.png is not byte "
            "identical to the brand master at "
            "docs/brand/recognitio-icon-512.png, so the package icon "
            "can drift from the brand record"
        )
    if (package / ".app.json").exists():
        problems.append(
            "agent-plugins-package/.app.json is present, but "
            "recognitio registers no MCP server apps"
        )
    if (root / ".codex-plugin").exists():
        problems.append(
            "a .codex-plugin directory stands at the repo root, but "
            "the com.openai extension replaces the compatibility "
            "overlay whole, so the overlay would be dead "
            "configuration"
        )


def marketplace_problems(root, problems):
    """Problems with the repo marketplace that offers the package."""
    data = load_json(root, ".agents/plugins/marketplace.json",
                     problems, "repo marketplace")
    if data is None:
        return
    if set(data) != {"name", "interface", "plugins"}:
        problems.append(
            "the repo marketplace fields are %r, not name, interface, "
            "and plugins" % sorted(data)
        )
    if data.get("name") != "recognitio":
        problems.append(
            "the repo marketplace name is %r, not recognitio"
            % (data.get("name"),)
        )
    if data.get("interface") != {"displayName": DISPLAY_NAME}:
        problems.append(
            "the repo marketplace interface is %r, not the single "
            "displayName Recognitio" % (data.get("interface"),)
        )
    plugins = data.get("plugins")
    if not isinstance(plugins, list) or len(plugins) != 1:
        problems.append(
            "the repo marketplace offers %r, not the single "
            "recognitio plugin" % (plugins,)
        )
        return
    entry = plugins[0]
    if not isinstance(entry, dict):
        problems.append("the repo marketplace entry is not an object")
        return
    if set(entry) != {"name", "source", "policy", "category"}:
        problems.append(
            "the repo marketplace entry fields are %r, not name, "
            "source, policy, and category" % sorted(entry)
        )
    if entry.get("name") != "recognitio":
        problems.append(
            "the repo marketplace entry names %r, not recognitio"
            % (entry.get("name"),)
        )
    source = entry.get("source")
    if source != {"source": "local", "path": "./agent-plugins-package"}:
        problems.append(
            "the repo marketplace source is %r, not the local source "
            "at ./agent-plugins-package" % (source,)
        )
    else:
        target = root / "agent-plugins-package" / "plugin.json"
        if not target.is_file():
            problems.append(
                "the repo marketplace source path resolves to no "
                "portable manifest"
            )
    if entry.get("policy") != {
        "installation": "AVAILABLE",
        "authentication": "ON_INSTALL",
    }:
        problems.append(
            "the repo marketplace policy is %r, not installation "
            "AVAILABLE with authentication ON_INSTALL"
            % (entry.get("policy"),)
        )
    if entry.get("category") != CATEGORY:
        problems.append(
            "the repo marketplace category is %r, not the plugin "
            "interface category %r" % (entry.get("category"), CATEGORY)
        )


def parse_openai_yaml(text):
    """Parse the two level openai.yaml shape into nested dicts.

    Only the shape the primary skills page documents is read, a
    top level mapping whose values are scalars or one nested
    mapping of scalars. A repeated key at either level returns
    None, like the strict JSON reader, so a second entry cannot
    hide beside the one the gate certifies. The result pairs
    the mapping with the set of dotted keys whose values arrived
    double quoted, because a quoted boolean is a string to a
    YAML reader and not the boolean the field declares. An
    unquoted value that opens with a hash returns None too,
    because YAML reads the hash as a comment and no scalar
    stands there at all. Anything else the reader cannot map
    returns None, so a shape the gate cannot read fails instead
    of passing in silence, and empty text parses to an empty
    mapping the caller's field pins then refuse.
    """
    parsed = {}
    quoted = set()
    current = None
    current_name = None
    for line in text.splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        indent = len(line) - len(line.lstrip(" "))
        stripped = line.strip()
        if ":" not in stripped:
            return None
        key, _, value = stripped.partition(":")
        key = key.strip()
        value = value.strip()
        was_quoted = (
            len(value) >= 2 and value[0] == '"' and value[-1] == '"'
        )
        if was_quoted:
            value = value[1:-1]
        elif value.startswith("#"):
            return None
        if indent == 0:
            if key in parsed:
                return None
            if value:
                parsed[key] = value
                if was_quoted:
                    quoted.add(key)
                current = None
                current_name = None
            else:
                current = {}
                parsed[key] = current
                current_name = key
        elif indent == 2 and current is not None:
            if not value or key in current:
                return None
            current[key] = value
            if was_quoted:
                quoted.add(current_name + "." + key)
        else:
            return None
    return parsed, quoted


def openai_yaml_problems(root, accent, problems):
    """Problems with the agents/openai.yaml skill folder file."""
    canonical = root / SKILL_TREES[0] / "agents" / "openai.yaml"
    if canonical.exists() and not canonical.is_file():
        problems.append(
            "the canonical agents/openai.yaml cannot be read, "
            "it is not a regular file")
        return
    try:
        canonical_bytes = canonical.read_bytes()
    except OSError:
        problems.append(
            "the canonical skill carries no agents/openai.yaml, so "
            "Codex gets no UI metadata or invocation policy for the "
            "skill"
        )
        return
    for tree in SKILL_TREES[1:]:
        copy = root / tree / "agents" / "openai.yaml"
        if copy.exists() and not copy.is_file():
            problems.append(
                "%s carries an agents/openai.yaml that cannot "
                "be read, it is not a regular file" % tree)
            continue
        try:
            copy_bytes = copy.read_bytes()
        except OSError:
            problems.append(
                "%s carries no agents/openai.yaml copy" % tree
            )
            continue
        if copy_bytes != canonical_bytes:
            problems.append(
                "%s/agents/openai.yaml is not byte identical to the "
                "canonical skill copy, so the skill spellings can "
                "drift" % tree
            )
    outcome = parse_openai_yaml(canonical_bytes.decode("utf-8"))
    if outcome is None:
        problems.append(
            "agents/openai.yaml does not parse in the two level "
            "shape the gate reads, or it repeats a key"
        )
        return
    parsed, quoted = outcome
    if set(parsed) != {"interface", "policy"}:
        problems.append(
            "agents/openai.yaml holds %r at the top level, not "
            "interface and policy, so it declares dependencies or "
            "another block the build does not ship" % sorted(parsed)
        )
        return
    interface = parsed["interface"]
    if not isinstance(interface, dict) or set(interface) != {
        "display_name",
        "short_description",
        "brand_color",
        "default_prompt",
    }:
        problems.append(
            "the openai.yaml interface holds %r, not the pinned "
            "display fields" % (interface,)
        )
    else:
        expected = {
            "display_name": DISPLAY_NAME,
            "short_description": SHORT_DESCRIPTION,
            "default_prompt": SKILL_DEFAULT_PROMPT,
        }
        for field, value in sorted(expected.items()):
            if interface.get(field) != value:
                problems.append(
                    "the openai.yaml interface %s is %r, not the "
                    "pinned value %r"
                    % (field, interface.get(field), value)
                )
        if accent is not None and interface.get("brand_color") != accent:
            problems.append(
                "the openai.yaml brand_color is %r, not the palette "
                "accent %r" % (interface.get("brand_color"), accent)
            )
    policy = parsed["policy"]
    if policy != {"allow_implicit_invocation": "true"}:
        problems.append(
            "the openai.yaml policy is %r, not "
            "allow_implicit_invocation left true, so the skill "
            "would stop triggering on a matching request" % (policy,)
        )
    if "policy.allow_implicit_invocation" in quoted:
        problems.append(
            "the openai.yaml policy value arrives quoted, so a "
            "YAML reader returns the string true and not the "
            "boolean the invocation policy declares"
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
    URL stems and Decision 4 are rare enough to match as
    substrings.
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
    parts = re.split(r"(?m)^### X\d+\.", section)
    blocks = parts[1:]
    if not blocks:
        return ["the rules section carries no X numbered rules"]
    for index, block in enumerate(blocks, start=1):
        flat = " ".join(block.split())
        if "Derives from" not in flat:
            problems.append(
                "rule X%d carries no derivation note, so it would "
                "be a rival instruction source" % index
            )
            continue
        note = flat.split("Derives from", 1)[1]
        if not deliberate_source(note):
            problems.append(
                "rule X%d names no canonical skill section, gate, "
                "or primary OpenAI citation in its derivation note"
                % index
            )
    return problems


def contradiction_problems(text, surface):
    """Problems with claims that contradict the honesty pins.

    The build's honesty rests on the negatives its sentences
    pin, that no universal directory listing exists or has
    been submitted and that invocation in a live session stays
    unverified, and on no surface standing verified for the
    desktop route. A presence pin cannot stop an appended
    sentence from claiming the opposite, so the contradicting
    stems are refused on every surface that carries the
    claims. The match is case folded, because a claim that
    opens a sentence capitalises its first word and the
    refusal has to hold there too.
    """
    problems = []
    folded = text.lower()
    for stem in CONTRADICTION_STEMS:
        if stem.lower() in folded:
            problems.append(
                "%s claims %r beside the pinned honesty sentences"
                % (surface, stem)
            )
    return problems


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


def brief_problems(root, problems):
    """Problems with the Build 19 brief and its records."""
    path = root / "docs" / "codex-plugin-brief.md"
    if path.exists() and not path.is_file():
        problems.append(
            "docs/codex-plugin-brief.md cannot be read, "
            "it is not a regular file")
        return
    try:
        raw = path.read_text(encoding="utf-8")
    except OSError:
        problems.append("docs/codex-plugin-brief.md is missing")
        return
    text = " ".join(raw.split())
    section = rules_section(raw)
    if section is None:
        problems.append(
            "docs/codex-plugin-brief.md carries no %r section"
            % RULES_HEADING
        )
    else:
        problems.extend(derivation_problems(section))
    problems.extend(
        contradiction_problems(text, "docs/codex-plugin-brief.md")
    )
    for label, sentence in BRIEF_SENTENCES:
        if sentence not in text:
            problems.append(
                "docs/codex-plugin-brief.md does not state %s, so "
                "the brief could drift from the primary record"
                % label
            )
    decisions = root / "docs" / "decisions.md"
    if decisions.exists() and not decisions.is_file():
        problems.append(
            "docs/decisions.md cannot be read, "
            "it is not a regular file")
        return
    try:
        record = decisions.read_text(encoding="utf-8")
    except OSError:
        problems.append("docs/decisions.md is missing")
        return
    start = record.find("## 29. Build 19")
    if start == -1:
        problems.append(
            "docs/decisions.md carries no decision 29 for Build 19"
        )
    else:
        section = record[start:]
        next_head = section.find("\n## ", 1)
        if next_head != -1:
            section = section[:next_head]
        if "Decision 4 binds" not in section:
            problems.append(
                "decision 29 carries no decision 4 statement"
            )
        problems.extend(
            contradiction_problems(
                " ".join(section.split()), "decision 29"
            )
        )
    changelog = root / "CHANGELOG.md"
    if changelog.exists() and not changelog.is_file():
        problems.append(
            "CHANGELOG.md cannot be read, "
            "it is not a regular file")
        return
    try:
        changelog_text = changelog.read_text(encoding="utf-8")
    except OSError:
        problems.append("CHANGELOG.md is missing")
        return
    marker = "\n- The Codex plugin build."
    start = changelog_text.find(marker)
    if start == -1:
        problems.append(
            "CHANGELOG.md carries no Codex plugin build entry"
        )
    else:
        bullet = changelog_text[start + 1:]
        stops = [
            spot
            for spot in (bullet.find("\n- ", 1), bullet.find("\n## ", 1))
            if spot != -1
        ]
        if stops:
            bullet = bullet[:min(stops)]
        problems.extend(
            contradiction_problems(
                " ".join(bullet.split()),
                "the CHANGELOG.md Codex plugin entry",
            )
        )
    index = root / "docs" / "README.md"
    if index.exists() and not index.is_file():
        problems.append(
            "docs/README.md cannot be read, "
            "it is not a regular file")
        return
    try:
        index_text = index.read_text(encoding="utf-8")
    except OSError:
        problems.append("docs/README.md is missing")
        return
    if "(codex-plugin-brief.md)" not in index_text:
        problems.append(
            "docs/README.md does not list the Codex plugin brief"
        )
    readme = root / "README.md"
    if readme.exists() and not readme.is_file():
        problems.append(
            "README.md cannot be read, "
            "it is not a regular file")
        return
    try:
        readme_text = readme.read_text(encoding="utf-8")
    except OSError:
        problems.append("README.md is missing")
        return
    link = "[the Codex plugin brief](docs/codex-plugin-brief.md)"
    if link not in readme_text:
        problems.append(
            "README.md does not link the Codex plugin brief from "
            "the adaptations table"
        )
    flat_readme = " ".join(readme_text.split())
    if README_INSTALL_SENTENCE not in flat_readme:
        problems.append(
            "README.md does not scope the Codex install route to "
            "the Plugins Directory of the ChatGPT desktop app, so "
            "the route reads as an install the CLI performs"
        )
    if README_STALE in flat_readme:
        problems.append(
            "README.md still carries the stale Codex install "
            "wording that promises an install the route does not "
            "perform"
        )
    problems.extend(contradiction_problems(flat_readme, "README.md"))
    for label, needle in (
        ("the Codex marketplace add command",
         "codex plugin marketplace add"),
        ("the Codex plugin add command", "codex plugin add"),
    ):
        if needle not in flat_readme:
            problems.append(
                "README.md does not state %s, so the install route "
                "the probe proved is not the route the README "
                "prints" % label
            )
    codex_start = readme_text.find("### Codex")
    if codex_start == -1:
        problems.append(
            "README.md carries no Codex install subsection"
        )
    else:
        codex_section = readme_text[codex_start:]
        stops = [
            spot
            for spot in (
                codex_section.find("\n### ", 1),
                codex_section.find("\n## ", 1),
            )
            if spot != -1
        ]
        if stops:
            codex_section = codex_section[:min(stops)]
        if not re.search(
            r"recognitio@recognitio(?![\w-])", codex_section
        ):
            problems.append(
                "README.md does not state the Codex plugin "
                "address recognitio@recognitio inside its Codex "
                "subsection, so the install route the probe "
                "proved is not the route the README prints"
            )
    agents = root / "AGENTS.md"
    if agents.exists() and not agents.is_file():
        problems.append(
            "AGENTS.md cannot be read, "
            "it is not a regular file")
        return
    try:
        agents_text = agents.read_text(encoding="utf-8")
    except OSError:
        problems.append("AGENTS.md is missing")
        return
    problems.extend(
        contradiction_problems(
            " ".join(agents_text.split()), "AGENTS.md"
        )
    )


def codex_plugin_problems(root=None):
    """Every Build 19 Codex plugin problem."""
    root = ROOT if root is None else root
    problems = []
    for rel in (
        "agent-plugins-package/plugin.json",
        "agent-plugins-package/assets/icon-512.png",
        ".agents/plugins/marketplace.json",
    ) + tuple(tree + "/agents/openai.yaml" for tree in SKILL_TREES):
        symlink_problems(root, rel, problems)
    accent = palette_accent(root, problems)
    manifest = load_json(
        root, "agent-plugins-package/plugin.json", problems,
        "portable manifest",
    )
    if manifest is not None:
        extension_problems(manifest, accent, problems)
    asset_problems(root, problems)
    marketplace_problems(root, problems)
    openai_yaml_problems(root, accent, problems)
    brief_problems(root, problems)
    return problems


def main(root=None):
    problems = codex_plugin_problems(root)
    if problems:
        for problem in problems:
            print("check_codex_plugin: %s" % problem, file=sys.stderr)
        return 1
    print("check_codex_plugin: the Build 19 Codex plugin build holds")
    return 0


if __name__ == "__main__":
    sys.exit(main())
