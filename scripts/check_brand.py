#!/usr/bin/env python3
"""Pin the visual round 8 brand asset contract.

The brand assets live under docs/brand beside their builder
and their palette record. This script pins the manifest
fields that name the assets and the fields that must stay
absent and the palette record and the master discipline so
a listing surface cannot drift away from the shipped assets
in silence. The asset measurements themselves stand in the
TestBrandAssets class of the gate script suite and this
script carries the manifest and palette logic of the brand
gate pins P1 and P2 and P3 and P9 and P10 and P11 and P16.
"""

import json
import re
import struct
import sys
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

CLAUDE_ICON = "./docs/brand/recognitio-icon-512.png"
CURSOR_LOGO = "docs/brand/recognitio-icon.svg"
BRAND_DIR = "docs/brand"
MASTERS = (
    "wordmark-light.svg",
    "wordmark-dark.svg",
    "recognitio-icon.svg",
    "recognitio-social-preview.svg",
)
IMAGE_KEYS = ("icon", "logo", "image", "banner", "logoUrl", "iconUrl")
OPENAI_NAMESPACE = "com.openai"
GITHUB_DARK_CANVAS = "#0D1117"
WHITE = "#FFFFFF"
DIFF_GREEN = "#3FB950"

EXPECTED_PALETTE = {
    "ground_dark": "#13151B",
    "ink_on_dark": "#E4E7EC",
    "ground_light": "#E4E7EC",
    "ink_on_light": "#13151B",
    "accent": "#D97757",
    "accent_secondary": "#79C0FF",
    "supporting_ink": "#B0B6C0",
    "frame_border": "#343842",
    "card_ground": "#181B23",
    "reserved_verified_green": "#4AC76A",
}


class DuplicateKeyError(ValueError):
    """A JSON object holds the same key twice."""


def _reject_duplicate_keys(pairs):
    out = {}
    for key, value in pairs:
        if key in out:
            raise DuplicateKeyError("repeated key %r" % (key,))
        out[key] = value
    return out


def strict_json_loads(text):
    return json.loads(text, object_pairs_hook=_reject_duplicate_keys)


def read_text(path):
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return None


def load_manifest(root, rel, problems):
    raw = read_text(root / rel)
    if raw is None:
        problems.append("missing manifest at %s" % rel)
        return None
    try:
        data = strict_json_loads(raw)
    except ValueError as exc:
        problems.append("%s does not parse and %s" % (rel, exc))
        return None
    if not isinstance(data, dict):
        problems.append("%s is not an object" % rel)
        return None
    return data


def find_image_keys(node):
    """Return the image field names inside one JSON value."""
    found = []
    if isinstance(node, dict):
        for key, value in node.items():
            if key in IMAGE_KEYS:
                found.append(key)
            found.extend(find_image_keys(value))
    elif isinstance(node, list):
        for value in node:
            found.extend(find_image_keys(value))
    return found


def manifest_problems(root=None):
    """Problems under pins P1 and P2 and P3 and P16."""
    root = ROOT if root is None else root
    problems = []
    claude = load_manifest(root, ".claude-plugin/plugin.json", problems)
    claude_market = load_manifest(
        root, ".claude-plugin/marketplace.json", problems)
    cursor = load_manifest(root, ".cursor-plugin/plugin.json", problems)
    cursor_market = load_manifest(
        root, ".cursor-plugin/marketplace.json", problems)
    portable = load_manifest(
        root, "agent-plugins-package/plugin.json", problems)
    zcode = load_manifest(root, ".zcode-plugin/plugin.json", problems)
    antigravity = load_manifest(root, ".antigravity/plugin.json", problems)

    # P1 field presence with the one spelling the field map records.
    if claude is not None and claude.get("icon") != CLAUDE_ICON:
        problems.append(
            ".claude-plugin/plugin.json carries no icon field with "
            "the brand value %s" % CLAUDE_ICON)
    if cursor is not None and cursor.get("logo") != CURSOR_LOGO:
        problems.append(
            ".cursor-plugin/plugin.json carries no logo field with "
            "the brand value %s" % CURSOR_LOGO)
    cursor_entry = None
    if cursor_market is not None:
        entries = cursor_market.get("plugins")
        if isinstance(entries, list) and entries:
            cursor_entry = entries[0]
    if cursor_entry is not None and cursor_entry.get("logo") != CURSOR_LOGO:
        problems.append(
            ".cursor-plugin/marketplace.json entry carries no logo "
            "field with the brand value %s" % CURSOR_LOGO)

    # P2 field absence on the surfaces that document no image field.
    if claude_market is not None:
        entries = claude_market.get("plugins")
        if isinstance(entries, list):
            for entry in entries:
                hits = find_image_keys(entry) if isinstance(entry, dict) else []
                if hits:
                    problems.append(
                        ".claude-plugin/marketplace.json entry carries "
                        "an image field %s and the icon lives in the "
                        "plugin manifest only" % hits[0])
    if portable is not None:
        top_hits = [key for key in portable if key in IMAGE_KEYS]
        if top_hits:
            problems.append(
                "agent-plugins-package/plugin.json carries an image "
                "field %s at the top level and its closed schema "
                "permits none" % top_hits[0])
        extensions = portable.get("extensions")
        if isinstance(extensions, dict):
            for namespace, value in extensions.items():
                if namespace == OPENAI_NAMESPACE:
                    continue
                hits = find_image_keys(value)
                if hits:
                    problems.append(
                        "agent-plugins-package/plugin.json carries an "
                        "image field %s inside the %s namespace and no "
                        "approved namespace holds one" % (hits[0], namespace))
    for rel, data in (
        (".zcode-plugin/plugin.json", zcode),
        (".antigravity/plugin.json", antigravity),
    ):
        if data is not None:
            hits = find_image_keys(data)
            if hits:
                problems.append(
                    "%s carries an image field %s and its surface "
                    "documents none" % (rel, hits[0]))

    # P3 path resolution and same file equality across the Cursor pair.
    resolved = {}
    for label, value in (
        (".claude-plugin/plugin.json icon", CLAUDE_ICON if claude is None else claude.get("icon")),
        (".cursor-plugin/plugin.json logo", CURSOR_LOGO if cursor is None else cursor.get("logo")),
        (".cursor-plugin/marketplace.json logo", CURSOR_LOGO if cursor_entry is None else cursor_entry.get("logo")),
    ):
        if not isinstance(value, str):
            continue
        target = root / value[2:] if value.startswith("./") else root / value
        resolved[label] = target
        if not target.is_file():
            problems.append(
                "%s names %s and that path resolves to no file in "
                "the repo" % (label, value))
    plugin_logo = resolved.get(".cursor-plugin/plugin.json logo")
    market_logo = resolved.get(".cursor-plugin/marketplace.json logo")
    if (plugin_logo is not None and market_logo is not None
            and plugin_logo.is_file() and market_logo.is_file()
            and plugin_logo.read_bytes() != market_logo.read_bytes()):
        problems.append(
            "the Cursor plugin logo and the Cursor marketplace logo "
            "resolve to different files and the pair must name one file")

    # P16 conditional field equality for an OpenAI namespace.
    problems.extend(openai_problems(root, portable))
    return problems


def openai_problems(root, portable):
    """Problems under the conditional pin P16."""
    if portable is None:
        return []
    extensions = portable.get("extensions")
    namespace = None
    if isinstance(extensions, dict):
        namespace = extensions.get(OPENAI_NAMESPACE)
    if namespace is None:
        raw = read_text(root / "agent-plugins-package/plugin.json") or ""
        claimed = [
            name for name in (
                "recognitio-icon", "recognitio-wordmark",
                "docs/brand", "brandColor",
            ) if name in raw
        ]
        if claimed:
            return [
                "agent-plugins-package/plugin.json claims the brand "
                "asset %s as shipped while no OpenAI namespace "
                "stands approved" % claimed[0]
            ]
        return []
    problems = []
    interface = namespace.get("interface") if isinstance(namespace, dict) else None
    if not isinstance(interface, dict):
        return [
            "the OpenAI namespace carries no interface object and "
            "its brand fields cannot be pinned"
        ]
    palette = load_palette(root, problems)
    accent = palette.get("accent") if palette else None
    if interface.get("brandColor") != accent:
        problems.append(
            "the OpenAI interface brandColor %r does not equal the "
            "palette accent %s" % (interface.get("brandColor"), accent))
    for key in ("composerIcon", "logo"):
        value = interface.get(key)
        if value is None:
            continue
        if not isinstance(value, str):
            problems.append("the OpenAI interface %s is not a path" % key)
            continue
        target = root / value[2:] if value.startswith("./") else root / value
        if not target.is_file():
            problems.append(
                "the OpenAI interface %s names %s and that path "
                "resolves to no file in the repo" % (key, value))
    shots = interface.get("screenshots")
    if isinstance(shots, list):
        for value in shots:
            if not isinstance(value, str):
                problems.append("an OpenAI interface screenshot is not a path")
                continue
            target = root / value[2:] if value.startswith("./") else root / value
            if not target.is_file():
                problems.append(
                    "an OpenAI interface screenshot names %s and "
                    "that path resolves to no file in the repo" % value)
    return problems


def load_palette(root, problems):
    raw = read_text(root / BRAND_DIR / "palette.json")
    if raw is None:
        problems.append("missing palette record at docs/brand/palette.json")
        return None
    try:
        data = strict_json_loads(raw)
    except ValueError as exc:
        problems.append("docs/brand/palette.json does not parse and %s" % exc)
        return None
    if not isinstance(data, dict):
        problems.append("docs/brand/palette.json is not an object")
        return None
    return data


def _channel(value):
    return value / 12.92 if value <= 0.03928 else ((value + 0.055) / 1.055) ** 2.4


def luminance(hex_value):
    vals = [int(hex_value[i:i + 2], 16) / 255.0 for i in (1, 3, 5)]
    lin = [_channel(v) for v in vals]
    return 0.2126 * lin[0] + 0.7152 * lin[1] + 0.0722 * lin[2]


def contrast(first, second):
    high = max(luminance(first), luminance(second))
    low = min(luminance(first), luminance(second))
    return (high + 0.05) / (low + 0.05)


def palette_problems(root=None):
    """Problems under pins P9 and P10."""
    root = ROOT if root is None else root
    problems = []
    palette = load_palette(root, problems)
    if palette is None:
        return problems
    for role, expected in EXPECTED_PALETTE.items():
        if palette.get(role) != expected:
            problems.append(
                "docs/brand/palette.json role %s holds %r and the "
                "frozen palette value is %s"
                % (role, palette.get(role), expected))
    pairs = (
        ("ink_on_dark", "ground_dark", 4.5, "wordmark ink on dark"),
        ("ink_on_light", "ground_light", 4.5, "wordmark ink on light"),
        ("accent", None, 3.0, "icon edge against white"),
        ("accent", "canvas", 3.0, "icon edge against the dark canvas"),
        ("ink_on_light", "accent", 3.0, "icon glyph against the tile"),
    )
    for first, second, floor, label in pairs:
        first_hex = palette.get(first)
        if second is None:
            second_hex = WHITE
        elif second == "canvas":
            second_hex = GITHUB_DARK_CANVAS
        else:
            second_hex = palette.get(second)
        if not (isinstance(first_hex, str) and isinstance(second_hex, str)):
            continue
        ratio = contrast(first_hex, second_hex)
        if ratio < floor:
            problems.append(
                "the palette pair for %s measures %.2f to 1 and the "
                "floor is %.1f to 1" % (label, ratio, floor))
    return problems


def _png_rows(path):
    """Return width and height and RGB rows for a PNG file.

    The decoder uses the standard library only and supports
    the 8 bit RGB and RGBA forms the brand exports ship in
    with no interlace.
    """
    raw = path.read_bytes()
    if raw[:8] != b"\x89PNG\r\n\x1a\n":
        raise AssertionError("not a PNG file")
    width, height, depth, color = struct.unpack(">IIBB", raw[16:26])
    if depth != 8 or color not in (2, 6) or raw[28] != 0:
        raise AssertionError("unexpected PNG form")
    channels = 3 if color == 2 else 4
    idat = bytearray()
    pos = 8
    animated = False
    while pos < len(raw):
        size = int.from_bytes(raw[pos:pos + 4], "big")
        kind = raw[pos + 4:pos + 8]
        if kind == b"IDAT":
            idat += raw[pos + 8:pos + 8 + size]
        if kind == b"acTL":
            animated = True
        pos += size + 12
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
        rows.append([
            tuple(line[i:i + 3]) for i in range(0, stride, channels)
        ])
        prev = line
    return width, height, rows, animated


def _geometry(text):
    """Return an SVG text with every fill and stroke colour removed."""
    return re.sub(r'(fill|stroke)="[^"]*"', r'\1=""', text)


def master_problems(root=None):
    """Problems under pins P9 and P11 and P13."""
    root = ROOT if root is None else root
    problems = []
    palette = load_palette(root, [])
    allowed = set()
    if palette:
        for role, value in palette.items():
            if role == "reserved_verified_green":
                continue
            if isinstance(value, str):
                allowed.add(value.upper())
    banned = set()
    if palette and isinstance(palette.get("reserved_verified_green"), str):
        banned.add(palette["reserved_verified_green"].upper())
    banned.add(DIFF_GREEN)
    texts = {}
    for name in MASTERS:
        raw = read_text(root / BRAND_DIR / name)
        if raw is None:
            problems.append("missing brand master at docs/brand/%s" % name)
            continue
        texts[name] = raw
        if "<text" in raw:
            problems.append(
                "docs/brand/%s carries a text element and brand "
                "lettering ships as paths only" % name)
        if "font-family" in raw or "fontFamily" in raw:
            problems.append(
                "docs/brand/%s carries a font family reference and "
                "brand lettering ships as paths only" % name)
        for marker in ("http://", "https://", "xlink:href", "url("):
            if marker == "http://":
                # The SVG namespace address is a name and not a fetch.
                scrubbed = raw.replace("http://www.w3.org/2000/svg", "")
                if marker in scrubbed:
                    problems.append(
                        "docs/brand/%s carries an external reference "
                        "and brand masters fetch nothing" % name)
                continue
            if marker in raw:
                problems.append(
                    "docs/brand/%s carries an external reference and "
                    "brand masters fetch nothing" % name)
        for hit in re.findall(r"#[0-9A-Fa-f]{6}\b", raw):
            if hit.upper() in banned:
                problems.append(
                    "docs/brand/%s uses the reserved green %s and no "
                    "brand asset may carry it" % (name, hit))
            elif allowed and hit.upper() not in allowed:
                problems.append(
                    "docs/brand/%s uses the colour %s and the palette "
                    "record names no such value" % (name, hit))
    light = texts.get("wordmark-light.svg")
    dark = texts.get("wordmark-dark.svg")
    if light is not None and dark is not None:
        if _geometry(light) != _geometry(dark):
            problems.append(
                "the wordmark masters differ in geometry and the "
                "two variants share one geometry with fills as "
                "the only difference")
    preview = root / BRAND_DIR / "recognitio-social-preview.png"
    if not preview.is_file():
        problems.append(
            "missing brand asset at docs/brand/recognitio-social-preview.png")
    elif palette and isinstance(palette.get("ground_dark"), str):
        try:
            _w, _h, rows, animated = _png_rows(preview)
        except (AssertionError, zlib.error, struct.error) as exc:
            problems.append(
                "docs/brand/recognitio-social-preview.png does not "
                "decode and %s" % exc)
        else:
            ground_hex = palette["ground_dark"]
            ground = tuple(
                int(ground_hex[i:i + 2], 16) for i in (1, 3, 5))
            corners = (rows[0][0], rows[0][-1], rows[-1][0], rows[-1][-1])
            if any(corner != ground for corner in corners):
                problems.append(
                    "the social preview corners are not the recorded "
                    "ground colour and the preview ground is solid")
            if animated:
                problems.append(
                    "the social preview carries an animation chunk "
                    "and the preview is a still image")
    return problems


def brand_problems(root=None):
    """Every brand asset problem this script pins."""
    problems = []
    problems.extend(manifest_problems(root))
    problems.extend(palette_problems(root))
    problems.extend(master_problems(root))
    return problems


def main(root=None):
    problems = brand_problems(root)
    if problems:
        for problem in problems:
            print("check_brand: %s" % problem, file=sys.stderr)
        return 1
    print("check_brand: the brand asset contract holds")
    return 0


if __name__ == "__main__":
    sys.exit(main())
