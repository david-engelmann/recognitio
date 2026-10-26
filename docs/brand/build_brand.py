#!/usr/bin/env python3
"""Build the recognitio brand assets from the palette record.

Every letter in every master is a path outlined from the
Liberation Sans font files on this machine with fontTools.
The fonts carry the SIL Open Font License version 1.1 and
that licence permits the outlining this builder performs.
No shipped SVG holds a text element or a font family
reference and no viewer machine can substitute a face into
the brand name.

The builder reads the palette record beside the assets and
generates the four master SVG files from it. It then renders
every PNG export through CairoSVG with an explicit output
width and an explicit output height and with no external
resource access. Each run prints the CairoSVG version and
the byte size and the SHA 256 digest of every output so a
regeneration can be compared digest for digest.
"""

import hashlib
import json
import sys
from pathlib import Path

import cairosvg
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.ttLib import TTFont

HERE = Path(__file__).resolve().parent
BOLD = "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"
REG = "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"

PALETTE = json.loads((HERE / "palette.json").read_text(encoding="utf-8"))
GROUND_DARK = PALETTE["ground_dark"]
INK_ON_DARK = PALETTE["ink_on_dark"]
INK_ON_LIGHT = PALETTE["ink_on_light"]
CORAL = PALETTE["accent"]
SUB = PALETTE["supporting_ink"]

TILE = 72.0
CHECK_W = 12.0
WORD_SIZE = 62.0

WORDMARK_NAME = "recognitio"
SOCIAL_NAME_SIZE = 80.0
SOCIAL_TILE = 92.0
TAGLINE_SIZE = 54.0
TAGLINE_LINES = (
    "A review starts from evidence",
    "instead of a bare diff",
)
TAGLINE_BASELINES = (368.0, 444.0)
SOCIAL_LOCK_Y = 176.0


def glyph_paths(font_path, text, size, tracking=1.0):
    """Return the path and advance per glyph plus the total.

    The return holds one entry per character in output units
    at the given size and a space character carries the
    advance of the space glyph itself.
    """
    font = TTFont(font_path)
    upm = font["head"].unitsPerEm
    scale = size / upm
    glyph_set = font.getGlyphSet()
    cmap = font.getBestCmap()
    hmtx = font["hmtx"]
    out = []
    total = 0.0
    for ch in text:
        if ch == " ":
            adv = hmtx[cmap[ord(" ")]][0] * scale * tracking
            out.append((None, adv))
            total += adv
            continue
        name = cmap[ord(ch)]
        pen = SVGPathPen(glyph_set)
        glyph_set[name].draw(pen)
        adv = hmtx[name][0] * scale * tracking
        out.append((pen.getCommands(), adv))
        total += adv
    return out, total, scale


def text_group(font_path, text, size, x, baseline, fill, tracking=1.0,
               anchor="start"):
    """Return one SVG group of outlined lettering as paths."""
    paths, total, scale = glyph_paths(font_path, text, size, tracking)
    if anchor == "middle":
        x = x - total / 2.0
    parts = []
    cx = x
    for data, adv in paths:
        if data:
            parts.append(
                '<path d="%s" fill="%s" transform="translate(%.2f %.2f) '
                'scale(%.5f -%.5f)"/>' % (data, fill, cx, baseline, scale, scale))
        cx += adv
    return "".join(parts), total


def check_points(cx, cy, r):
    """Return the three points of the check glyph.

    The points mirror the check the demo builder draws with
    a left point and an inner corner and an upper right point.
    """
    return "%.2f,%.2f %.2f,%.2f %.2f,%.2f" % (
        cx - r + 3, cy, cx - 1, cy + r - 3, cx + r - 3, cy - r + 4)


def mark_group(origin_x, origin_y, tile, check_w):
    """Return the coral tile with the dark check glyph on it."""
    cx = origin_x + tile / 2.0
    cy = origin_y + tile / 2.0
    r = tile * 0.30
    return (
        '<rect x="%.2f" y="%.2f" width="%.2f" height="%.2f" rx="%.2f" '
        'fill="%s"/>'
        '<polyline points="%s" fill="none" stroke="%s" '
        'stroke-width="%.2f" stroke-linecap="round" '
        'stroke-linejoin="round"/>'
        % (origin_x, origin_y, tile, tile, tile * 0.26, CORAL,
           check_points(cx, cy, r), INK_ON_LIGHT, check_w))


def icon_svg():
    """Return the icon master with the tile at 72 percent."""
    off = (100.0 - TILE) / 2.0
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100" '
        'width="512" height="512" role="img" aria-label="recognitio">'
        + mark_group(off, off, TILE, CHECK_W) + "</svg>\n")


def wordmark_svg(ink):
    """Return one wordmark master in the given lettering ink.

    Both variants share this one geometry and the fills are
    the only difference between the light and dark masters.
    """
    tile = 72.0
    off = 14.0
    size = WORD_SIZE
    _paths, total, _scale = glyph_paths(BOLD, WORDMARK_NAME, size, 0.99)
    width = off + tile + 20.0 + total + off
    baseline = off + tile / 2.0 + size * 0.35
    text, _total = text_group(BOLD, WORDMARK_NAME, size, off + tile + 20.0,
                              baseline, ink, 0.99)
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %.2f 100" '
        'width="%.0f" height="100" role="img" aria-label="recognitio">'
        % (width, width)
        + mark_group(off, off, tile, CHECK_W) + text + "</svg>\n"), width


def social_svg():
    """Return the social preview master at 1280 by 640.

    The lockup stands centred and wholly inside the central
    640 by 640 region of the canvas. The tagline is the README
    headline in two lines under the lockup and every line
    stands inside the side inset and the whole block stands
    inside the top and bottom inset.
    """
    w, h = 1280.0, 640.0
    tile = SOCIAL_TILE
    name_size = SOCIAL_NAME_SIZE
    _paths, name_w, _scale = glyph_paths(BOLD, WORDMARK_NAME, name_size, 0.99)
    lock_w = tile + 26.0 + name_w
    lock_x = (w - lock_w) / 2.0
    lock_y = SOCIAL_LOCK_Y
    name_base = lock_y + tile / 2.0 + name_size * 0.35
    parts = ['<rect width="1280" height="640" fill="%s"/>' % GROUND_DARK]
    parts.append(mark_group(lock_x, lock_y, tile, CHECK_W * tile / 72.0))
    text, _total = text_group(BOLD, WORDMARK_NAME, name_size,
                              lock_x + tile + 26.0, name_base, INK_ON_DARK, 0.99)
    parts.append(text)
    for line, baseline in zip(TAGLINE_LINES, TAGLINE_BASELINES):
        text, _total = text_group(REG, line, TAGLINE_SIZE, w / 2.0, baseline,
                                  SUB, 1.0, anchor="middle")
        parts.append(text)
    return ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1280 640" '
            'width="1280" height="640" role="img" aria-label="recognitio">'
            + "".join(parts) + "</svg>\n")


def render_png(svg_path, png_path, width, height):
    """Render one PNG export through CairoSVG at a fixed size."""
    cairosvg.svg2png(
        url=str(svg_path),
        write_to=str(png_path),
        output_width=width,
        output_height=height,
        unsafe=False,
    )


def main():
    masters = {}
    dark, word_width = wordmark_svg(INK_ON_DARK)
    light, _width = wordmark_svg(INK_ON_LIGHT)
    masters["wordmark-dark.svg"] = dark
    masters["wordmark-light.svg"] = light
    masters["recognitio-icon.svg"] = icon_svg()
    masters["recognitio-social-preview.svg"] = social_svg()
    for name, text in masters.items():
        (HERE / name).write_text(text, encoding="utf-8")
    word_height = int(round(1600 * 100 / word_width))
    exports = (
        ("wordmark-light.svg", "recognitio-wordmark-1600.png", 1600, word_height),
        ("recognitio-icon.svg", "recognitio-icon-512.png", 512, 512),
        ("recognitio-icon.svg", "recognitio-icon-256.png", 256, 256),
        ("recognitio-social-preview.svg", "recognitio-social-preview.png", 1280, 640),
    )
    for source, target, width, height in exports:
        render_png(HERE / source, HERE / target, width, height)
    outputs = list(masters) + [target for _s, target, _w, _h in exports]
    print("CairoSVG version %s" % cairosvg.__version__)
    for name in outputs:
        data = (HERE / name).read_bytes()
        print("%s %d %s" % (name, len(data), hashlib.sha256(data).hexdigest()))
    return 0


if __name__ == "__main__":
    sys.exit(main())
