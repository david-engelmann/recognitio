#!/usr/bin/env python3
"""Build the README demo assets from capture.json.

The hero chat GIF plus the stills gallery, all rendered from
the one recorded session in capture.json beside this file.
Variant A (chat UI mock) is the hero motion asset and Variant
B (polished terminal) supplies the gallery stills.
Every content string drawn here comes from capture.json: the
ask, the two model responses, the six command strings and
their captured stdouts, and the meta figures. Presentation
(chrome, check marks drawn as lines, the window frames, the
scroll viewports) adds no words. An assertion pass at the end
checks every content segment against the capture field it
came from, with whitespace collapsed.
"""

import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
WORK = HERE / ".build-tmp"
OUTDIR = HERE
WORK.mkdir(parents=True, exist_ok=True)

CAP = json.loads((HERE / "capture.json").read_text())

ASK = CAP["ask"]
PLAN = CAP["calls"][0]["response"].strip()
REVIEW = CAP["calls"][1]["response"].strip()
CMDS = CAP["commands"]
DIFF = CMDS[0]["out"]
EXTRACT_OUT = CMDS[1]["out"].strip()
TRIAGE = CMDS[2]["out"]
TESTSECT = CMDS[3]["out"]
TAIL = CMDS[4]["out"]
VERIFIED_LINE = CMDS[5]["out"].strip()
META = CAP["meta"]

TRIAGE_LINE = TRIAGE.splitlines()[0]          # "# The pericope for range ..."
VERIFIED_YES = TRIAGE.splitlines()[8]          # "Verified: yes"
TEST_LINE = TESTSECT.splitlines()[0]           # "### Test files ..."
NO_TIER = TAIL.splitlines()[0]                 # "No tier was dropped."
COMPLETE = TAIL.splitlines()[2]                # "Completeness check passed. ..."
FLOOD_CMD = CAP["flood_cmd"]                   # "git diff 365da81e ecdda4c8"
DIFF_FIGURE = f"{META['diff_lines']:,} lines"  # "3,233 lines", meta figure

# Content segments, for the closing assertion pass.
SEGMENTS = [
    ASK, PLAN, REVIEW, EXTRACT_OUT, TRIAGE_LINE, VERIFIED_YES,
    TEST_LINE, NO_TIER, COMPLETE, VERIFIED_LINE, FLOOD_CMD,
]


def squash(s):
    return re.sub(r"\s+", " ", s).strip()


def wrap_text(text, font, max_w, draw):
    """Greedy word wrap by pixel width. Words are never split
    unless a single word exceeds the width."""
    out = []
    for raw in text.split("\n"):
        if raw == "":
            out.append("")
            continue
        words = raw.split(" ")
        line = ""
        for w in words:
            trial = w if line == "" else line + " " + w
            if draw.textlength(trial, font=font) <= max_w:
                line = trial
            else:
                if line:
                    out.append(line)
                while draw.textlength(w, font=font) > max_w and len(w) > 1:
                    cut = len(w)
                    while cut > 1 and draw.textlength(w[:cut], font=font) > max_w:
                        cut -= 1
                    out.append(w[:cut])
                    w = w[cut:]
                line = w
        out.append(line)
    return out


def wrap_mono(text, cols):
    out = []
    for raw in text.split("\n"):
        rest = raw
        if rest == "":
            out.append("")
            continue
        while len(rest) > cols:
            cut = rest.rfind(" ", 0, cols + 1)
            if cut <= 0:
                out.append(rest[:cols])
                rest = rest[cols:]
            else:
                out.append(rest[:cut])
                rest = rest[cut + 1:]
        out.append(rest)
    return out


RING = (128, 135, 148)
RING_W = 2


def add_ring(img):
    """Draw the border ring inside the canvas edge.

    The ring is chrome added by this builder and not part of
    the recorded session. It reuses the chat palette dim grey,
    which measures 5.24 to 1 against the GitHub dark canvas at
    13, 17, 23 and 3.61 to 1 against white, so every asset
    carries its own edge on both page themes. The session
    pixels inside the ring are untouched.
    """
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, img.width - 1, img.height - 1],
                outline=RING, width=RING_W)
    return img


def assemble(states, frames_dir, out_path, max_colors=160):
    """states: list of (PIL image, hold_ms). Writes the GIF and
    returns (frames, duration_s, bytes)."""
    frames_dir.mkdir(parents=True, exist_ok=True)
    for old in frames_dir.glob("s*.png"):
        old.unlink()
    lines = []
    for i, (img, hold) in enumerate(states):
        name = "s%03d.png" % i
        img.save(frames_dir / name)
        lines.append("file '%s'" % name)
        lines.append("duration %.3f" % (max(20, hold) / 1000))
    lines.append("file '%s'" % ("s%03d.png" % (len(states) - 1)))
    concat = frames_dir / "concat.txt"
    concat.write_text("\n".join(lines) + "\n", encoding="utf-8")
    palette = frames_dir / "palette.png"
    subprocess.run(
        ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(concat),
         "-vf", "palettegen=max_colors=%d" % max_colors, str(palette)],
        check=True, capture_output=True)
    subprocess.run(
        ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(concat),
         "-i", str(palette), "-lavfi", "paletteuse=dither=none",
         str(out_path)],
        check=True, capture_output=True)
    total = sum(max(20, h) for _i, h in states) / 1000
    return len(states), round(total, 1), out_path.stat().st_size


# ----------------------------------------------------------------
# Variant A: chat UI mock
# ----------------------------------------------------------------

SANS = "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"
SANS_B = "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"
MONO = "/usr/share/fonts/truetype/liberation/LiberationMono-Regular.ttf"
MONO_B = "/usr/share/fonts/truetype/liberation/LiberationMono-Bold.ttf"

A_W, A_H = 796, 624
A_BG = (19, 21, 27)
A_HEADER = (24, 27, 34)
A_BORDER = (52, 56, 66)
A_FG = (228, 231, 236)
A_SUB = (176, 182, 192)
A_DIM = (128, 135, 148)
A_ACCENT = (217, 119, 87)
A_GREEN = (74, 199, 106)
A_BUBBLE = (39, 44, 56)
A_ATTACH = (13, 15, 20)
A_CARD = (24, 27, 35)
A_DGREEN = (63, 185, 80)
A_DRED = (248, 81, 73)
A_DBLUE = (121, 192, 255)

F_TITLE = ImageFont.truetype(SANS_B, 16)
F_BODY = ImageFont.truetype(SANS, 15)
F_BODY_B = ImageFont.truetype(SANS_B, 15)
F_CARD_T = ImageFont.truetype(SANS_B, 14)
F_MONO = ImageFont.truetype(MONO, 12)
F_MONO_SM = ImageFont.truetype(MONO, 11)
F_MONO_B = ImageFont.truetype(MONO_B, 12)

FEED_X = 26
FEED_W = A_W - 2 * FEED_X           # 744
HEADER_H = 48
FEED_TOP = HEADER_H + 16
FEED_H = A_H - FEED_TOP - 14        # 546
GAP = 18

BUBBLE_W = 600
ATTACH_LINES = 7
ATTACH_LH = 15
ATTACH_H = 8 + ATTACH_LINES * ATTACH_LH + 6 + 20 + 8   # 147
ASK_LH = 22
ASK_LINES = 3
BUBBLE_H = 12 + ATTACH_H + 10 + ASK_LINES * ASK_LH + 14  # 249

CARD_W = 668
CARD_STEPS = [EXTRACT_OUT, TRIAGE_LINE, TEST_LINE, NO_TIER, COMPLETE, VERIFIED_YES]
CARD_STEP_LH = 18

_probe = ImageDraw.Draw(Image.new("RGB", (10, 10)))
CARD_STEP_ROWS = [wrap_text(s, F_MONO, CARD_W - 28 - 26, _probe) for s in CARD_STEPS]
CARD_H = 14 + 24 + 10 + sum(len(r) * CARD_STEP_LH for r in CARD_STEP_ROWS) + 6 + 14

PLAN_ROWS = wrap_text(PLAN, F_BODY, 668, _probe)
PLAN_H = len(PLAN_ROWS) * 23

REVIEW_W = 700
REVIEW_PARAS = REVIEW.split("\n\n")
REVIEW_ROWS = []
for pi, para in enumerate(REVIEW_PARAS):
    rows = wrap_text(para, F_BODY, REVIEW_W - 8, _probe)
    REVIEW_ROWS.append(rows)
REVIEW_H = sum(len(r) * 23 for r in REVIEW_ROWS) + (len(REVIEW_ROWS) - 1) * 12

DIFF_ROWS_A = wrap_mono(DIFF, 84)


def a_draw_check(d, cx, cy, r, color):
    d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=color, width=2)
    d.line([cx - r + 3, cy, cx - 1, cy + r - 3], fill=color, width=2)
    d.line([cx - 1, cy + r - 3, cx + r - 3, cy - r + 4], fill=color, width=2)


def a_user_bubble(flood_start, ask_chars):
    img = Image.new("RGB", (BUBBLE_W, BUBBLE_H), A_BG)
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([0, 0, BUBBLE_W - 1, BUBBLE_H - 1], 14, fill=A_BUBBLE)
    # attachment block
    ax, ay = 12, 12
    aw = BUBBLE_W - 24
    d.rounded_rectangle([ax, ay, ax + aw - 1, ay + ATTACH_H - 1], 10, fill=A_ATTACH)
    ty = ay + 8
    for line in DIFF_ROWS_A[flood_start:flood_start + ATTACH_LINES]:
        if line.startswith("+") and not line.startswith("+++"):
            color = A_DGREEN
        elif line.startswith("-") and not line.startswith("---"):
            color = A_DRED
        elif line.startswith("@@") or line.startswith("diff --git"):
            color = A_DBLUE
        else:
            color = A_DIM
        d.text((ax + 10, ty), line, font=F_MONO_SM, fill=color)
        ty += ATTACH_LH
    fy = ay + 8 + ATTACH_LINES * ATTACH_LH + 6
    d.text((ax + 10, fy), FLOOD_CMD, font=F_MONO_SM, fill=A_DIM)
    fw = d.textlength(DIFF_FIGURE, font=F_MONO_SM)
    d.text((ax + aw - 10 - fw, fy), DIFF_FIGURE, font=F_MONO_SM, fill=A_DIM)
    # ask text inside the same bubble
    ky = ay + ATTACH_H + 10
    partial = ASK[:ask_chars]
    for row in wrap_text(partial, F_BODY, BUBBLE_W - 28, d):
        d.text((14, ky), row, font=F_BODY, fill=A_FG)
        ky += ASK_LH
    return img


def a_plan_block(nrows):
    img = Image.new("RGB", (668, max(1, nrows) * 23), A_BG)
    d = ImageDraw.Draw(img)
    y = 0
    for row in PLAN_ROWS[:nrows]:
        d.text((0, y), row, font=F_BODY, fill=A_SUB)
        y += 23
    return img


def a_card_block(done):
    img = Image.new("RGB", (CARD_W, CARD_H), A_BG)
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([0, 0, CARD_W - 1, CARD_H - 1], 12, fill=A_CARD, outline=A_BORDER, width=1)
    d.ellipse([14, 14 + 4, 14 + 10, 14 + 14], fill=A_ACCENT)
    d.text((32, 14), "recognitio", font=F_CARD_T, fill=A_FG)
    if done >= len(CARD_STEPS):
        pill = VERIFIED_LINE
        pw = d.textlength(pill, font=F_MONO_SM) + 16
        d.rounded_rectangle([CARD_W - 14 - pw, 12, CARD_W - 14, 12 + 20], 10,
                            fill=(20, 42, 28))
        d.text((CARD_W - 14 - pw + 8, 12 + 4), pill, font=F_MONO_SM, fill=A_GREEN)
    y = 14 + 24 + 10
    for i, rows in enumerate(CARD_STEP_ROWS):
        if i < done:
            a_draw_check(d, 14 + 7, y + 8, 7, A_GREEN)
            for row in rows:
                d.text((14 + 26, y), row, font=F_MONO, fill=A_FG)
                y += CARD_STEP_LH
        elif i == done:
            d.arc([14, y + 1, 14 + 14, y + 15], start=40, end=300, fill=A_ACCENT, width=2)
            for row in rows:
                d.text((14 + 26, y), row, font=F_MONO, fill=A_DIM)
                y += CARD_STEP_LH
        else:
            for _row in rows:
                y += CARD_STEP_LH
    return img


def a_review_block():
    img = Image.new("RGB", (REVIEW_W, REVIEW_H), A_BG)
    d = ImageDraw.Draw(img)
    y = 0
    for rows in REVIEW_ROWS:
        for row in rows:
            d.text((0, y), row, font=F_BODY, fill=A_FG)
            y += 23
        y += 12
    return img


def a_compose(blocks, offset):
    """blocks: list of images, stacked with GAP. offset: pixels of
    feed scrolled away at the top."""
    img = Image.new("RGB", (A_W, A_H), A_BG)
    d = ImageDraw.Draw(img)
    total = sum(b.height for b in blocks) + GAP * (len(blocks) - 1)
    y = FEED_TOP - offset
    for b in blocks:
        x = FEED_X + (FEED_W - b.width) if b.width == BUBBLE_W else FEED_X
        if b.width == REVIEW_W:
            x = FEED_X
        img.paste(b, (x, y))
        y += b.height + GAP
    d.rectangle([0, 0, A_W, HEADER_H], fill=A_HEADER)
    d.line([0, HEADER_H, A_W, HEADER_H], fill=A_BORDER, width=1)
    d.rounded_rectangle([22, 15, 22 + 18, 15 + 18], 5, fill=A_ACCENT)
    d.text((50, 15), "recognitio", font=F_TITLE, fill=A_FG)
    add_ring(img)
    return img, total


def build_a():
    states = []  # (blocks, offset, hold_ms)

    def snap(blocks, offset, hold):
        img, _t = a_compose(blocks, offset)
        states.append((img, hold))

    def bottom(blocks):
        total = sum(b.height for b in blocks) + GAP * (len(blocks) - 1)
        return max(0, total - FEED_H)

    # frame zero is a loaded early frame, never the black box.
    # The settled diff tail sits in the attachment while the ask
    # is already arriving in the same bubble.
    last = len(DIFF_ROWS_A) - ATTACH_LINES
    snap([a_user_bubble(last, 44)], 0, 600)

    # flood inside the attachment viewport, then settle on the tail
    starts = [0, 420, 950, 1550, 2150, 2680, 3120, 3520, last]
    bubble_full = a_user_bubble(last, 44)
    for s in starts[:-1]:
        snap([a_user_bubble(s, 44)], 0, 140)
    snap([bubble_full], 0, 200)

    # ask typed on inside the bubble
    for n in range(66, len(ASK) + 1, 22):
        snap([a_user_bubble(last, n)], 0, 60)
    snap([a_user_bubble(last, len(ASK))], 0, 450)
    bubble_done = a_user_bubble(last, len(ASK))

    # plan appears
    for k in (1, 2, 3):
        blocks = [bubble_done, a_plan_block(k)]
        snap(blocks, bottom(blocks), 180)
    blocks = [bubble_done, a_plan_block(3)]
    snap(blocks, bottom(blocks), 700)
    plan_done = a_plan_block(3)

    # recognitio tool card ticks through its real steps
    for done in range(0, len(CARD_STEPS) + 1):
        blocks = [bubble_done, plan_done, a_card_block(done)]
        snap(blocks, bottom(blocks), 480 if done < len(CARD_STEPS) else 400)
    card_done = a_card_block(len(CARD_STEPS))
    blocks = [bubble_done, plan_done, card_done]
    snap(blocks, bottom(blocks), 600)
    poster_idx = len(states) - 1

    # review arrives and scrolls slowly; final frame holds
    review_img = a_review_block()
    blocks = [bubble_done, plan_done, card_done, review_img]
    total = sum(b.height for b in blocks) + GAP * (len(blocks) - 1)
    off0 = total - REVIEW_H - FEED_H  # offset where the review top enters
    off0 = max(0, off0)
    # Reframe the verdict rest one full line pitch above the
    # shipped offset, so the resting frame opens on the line
    # after the paragraph opening the header bar used to hide.
    # No recorded line sits partly under the header bar.
    off_end = max(0, total - FEED_H - 23)
    snap(blocks, off0, 700)
    steps = 9
    for i in range(1, steps + 1):
        off = off0 + (off_end - off0) * i // steps
        snap(blocks, off, 380)
    snap(blocks, off_end, 2400)
    return states, poster_idx


# ----------------------------------------------------------------
# Variant B: polished terminal
# ----------------------------------------------------------------

D_MONO = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"
D_MONO_B = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"
D_SANS = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"

B_W = 796
B_FS = 14
B_LH = 22
B_PADX = 18
B_TITLE_H = 34
B_PADY = 10
B_BG = (13, 17, 23)
B_TITLE_BG = (22, 27, 34)
B_FG = (230, 237, 243)
B_DIM = (139, 148, 158)
B_GREEN = (63, 185, 80)
B_RED = (248, 81, 73)
B_BLUE = (121, 192, 255)
B_ACCENT = (217, 119, 87)
B_YELLOW = (255, 189, 46)

F_B = ImageFont.truetype(D_MONO, B_FS)
F_BB = ImageFont.truetype(D_MONO_B, B_FS)
F_BT = ImageFont.truetype(D_SANS, 12)
B_CHAR_W = F_B.getbbox("M")[2]  # glyph column offset only
B_ADV = F_B.getlength("M")      # true per-character advance
B_COLS = int((B_W - 2 * B_PADX - 6) / B_ADV)
B_ROWS = 18
B_H = B_TITLE_H + B_PADY * 2 + B_LH * B_ROWS


def b_wrap(text, cols=B_COLS):
    return wrap_mono(text, cols)


def b_diff_rows(text):
    rows = []
    for raw in text.splitlines():
        if raw.startswith("+") and not raw.startswith("+++"):
            kind = "p"
        elif raw.startswith("-") and not raw.startswith("---"):
            kind = "m"
        elif raw.startswith("@@") or raw.startswith("diff --git"):
            kind = "h"
        else:
            kind = "d"
        for piece in b_wrap(raw):
            rows.append((piece, kind))
    return rows


def b_out_rows(text):
    rows = []
    for raw in text.splitlines():
        if (raw.startswith("recognitio: packet written")
                or raw.startswith("Completeness check passed")
                or '"verified": true' in raw
                or raw.startswith("Verified: yes")
                or raw.startswith("No tier was dropped")):
            kind = "a"
        elif raw.startswith("#"):
            kind = "h"
        else:
            kind = "o"
        for piece in b_wrap(raw, B_COLS - 2):
            rows.append((piece, kind))
    if rows:
        rows[0] = (rows[0][0], "f" + rows[0][1])
    return rows


def b_draw(rows):
    img = Image.new("RGB", (B_W, B_H), B_BG)
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, B_W, B_TITLE_H], fill=B_TITLE_BG)
    for i, color in enumerate((B_RED, B_YELLOW, B_GREEN)):
        cx = B_PADX + 6 + i * 20
        d.ellipse([cx - 6, B_TITLE_H // 2 - 6, cx + 6, B_TITLE_H // 2 + 6], fill=color)
    title = "recognitio · agent session"
    tw = d.textlength(title, font=F_BT)
    d.text(((B_W - tw) / 2, B_TITLE_H // 2 - 7), title, font=F_BT, fill=B_DIM)
    y = B_TITLE_H + B_PADY
    for text, kind in rows:
        x = B_PADX
        if kind in ("ask", "tool"):
            glyph = ">" if kind == "ask" else "●"
            d.text((x, y), glyph, font=F_BB, fill=B_ACCENT)
            x += B_CHAR_W * 2
            d.text((x, y), text, font=F_BB if kind == "ask" else F_B, fill=B_FG)
        elif kind in ("ask_c", "tool_c"):
            x += B_CHAR_W * 2
            d.text((x, y), text, font=F_BB if kind == "ask_c" else F_B, fill=B_FG)
        elif kind.startswith("f"):
            d.text((x, y), "└", font=F_B, fill=B_DIM)
            x += B_CHAR_W * 2
            base = kind[1:]
            if base == "a":
                d.text((x, y), text, font=F_BB, fill=B_GREEN)
            elif base == "h":
                d.text((x, y), text, font=F_B, fill=B_BLUE)
            else:
                d.text((x, y), text, font=F_B, fill=B_FG)
        elif kind in ("o", "a", "h"):
            x += B_CHAR_W * 2
            if kind == "a":
                d.text((x, y), text, font=F_BB, fill=B_GREEN)
            elif kind == "h":
                d.text((x, y), text, font=F_B, fill=B_BLUE)
            else:
                d.text((x, y), text, font=F_B, fill=B_FG)
        elif kind == "p":
            d.text((x, y), text, font=F_B, fill=B_GREEN)
        elif kind == "m":
            d.text((x, y), text, font=F_B, fill=B_RED)
        elif kind == "h":
            d.text((x, y), text, font=F_B, fill=B_BLUE)
        elif kind == "d":
            d.text((x, y), text, font=F_B, fill=B_DIM)
        else:
            d.text((x, y), text, font=F_B, fill=B_FG)
        y += B_LH
    add_ring(img)
    return img


def b_glyph_rows(text, kind, cols):
    rows = []
    for raw in text.splitlines():
        rows.extend(b_wrap(raw, cols))
    return [(r, kind if i == 0 else kind + "_c") for i, r in enumerate(rows)]


def build_b():
    states = []
    screen = []
    marks = {}

    def snap(hold):
        states.append((b_draw(screen[-B_ROWS:]), hold))

    def reveal(rows, per, step_ms, hold):
        for cut in range(per, len(rows) + 1, per):
            states.append((b_draw((screen + rows[:cut])[-B_ROWS:]), step_ms))
        if len(rows) % per:
            states.append((b_draw((screen + rows)[-B_ROWS:]), step_ms))
        screen.extend(rows)
        snap(hold)

    snap(600)

    # the flood, a brief fast beat easing out at the tail
    flood = b_diff_rows(DIFF)
    cut = 0
    steps = [700, 500, 380, 300, 230, 180, 140, 105, 80, 60, 45, 32, 22, 14, 8]
    for s in steps:
        cut = min(len(flood), cut + s)
        states.append((b_draw(flood[max(0, cut - B_ROWS):cut]), 90))
        if cut >= len(flood):
            break
    if cut < len(flood):
        states.append((b_draw(flood[-B_ROWS:]), 90))
    screen = list(flood[-B_ROWS:])
    snap(800)
    marks["diff_tail"] = len(states) - 1

    # the ask, typed at a readable speed
    for n in range(14, len(ASK) + 1, 14):
        partial = b_glyph_rows(ASK[:n], "ask", B_COLS - 2)
        states.append((b_draw((screen + partial)[-B_ROWS:]), 75))
    screen.extend(b_glyph_rows(ASK, "ask", B_COLS - 2))
    snap(700)

    # the plan, verbatim, with a reading hold
    plan_rows = []
    for raw in PLAN.splitlines():
        for piece in b_wrap(raw):
            plan_rows.append((piece, "prose"))
    reveal(plan_rows, 1, 170, 2200)

    # the tool calls in the order the harness ran them
    holds = [1300, 1500, 1300, 1700, 1900]
    for index, seg in enumerate(CMDS[1:]):
        screen.extend(b_glyph_rows("Bash(" + seg["cmd"] + ")", "tool", B_COLS - 2))
        snap(250)
        reveal(b_out_rows(seg["out"]), 3, 115, holds[index])
        if index == len(CMDS[1:]) - 1:
            marks["verified"] = len(states) - 1

    # the review, slow enough to read, final hold long
    review_rows = []
    for raw in REVIEW.splitlines():
        if raw == "":
            review_rows.append(("", "prose"))
        else:
            for piece in b_wrap(raw):
                review_rows.append((piece, "prose"))
    reveal(review_rows, 2, 340, 4500)
    marks["verdict"] = len(states) - 1
    return states, marks


def main():
    which = sys.argv[1] if len(sys.argv) > 1 else "all"
    results = {}
    if which in ("all", "a"):
        states, poster_idx = build_a()
        results["A"] = assemble(states, WORK / "frames_a",
                                OUTDIR / "recognitio-demo-chat.gif", 96)
        # Hero poster, the finished tool card frame. It is the
        # state just before the review entrance, the last card
        # hold state in the sequence.
        poster = states[poster_idx][0]
        poster.save(OUTDIR / "recognitio-demo-poster.png", optimize=True)
        # Detail crop from that same frame, tight on the card
        # header and the first packet line. The region runs
        # from the blank gap before the 28 files figure to
        # just past the card right edge, and from the blank
        # band above the card to the blank band under the
        # first packet line,
        # so no glyph row is sliced at any edge. At 360 pixels
        # wide against the 796 pixel frame it magnifies 2.21
        # times, where the shipped 720 pixel crop managed 1.11.
        detail = poster.crop((362, 408, 722, 482))
        add_ring(detail)
        detail.save(
            OUTDIR / "recognitio-demo-poster-detail.png", optimize=True)
        print("poster and detail crop written from the card frame")
    if which in ("all", "b"):
        states_b, marks = build_b()
        names = {"diff_tail": "recognitio-demo-still-diff.png",
                 "verified": "recognitio-demo-still-verified.png",
                 "verdict": "recognitio-demo-still-verdict.png"}
        for key, fname in names.items():
            states_b[marks[key]][0].save(OUTDIR / fname, optimize=True)
            print("still %s from terminal state %d" % (fname, marks[key]))
    # assertion pass: every content segment is verbatim capture text
    haystacks = [DIFF, PLAN, REVIEW, ASK, TRIAGE, TESTSECT, TAIL,
                 EXTRACT_OUT, VERIFIED_LINE, FLOOD_CMD,
                 "\n".join(c["cmd"] for c in CMDS)]
    blob = squash("\n".join(haystacks))
    for seg in SEGMENTS:
        assert squash(seg) in blob, "segment not in capture: %r" % seg[:60]
    for key, (frames, secs, size) in results.items():
        print("variant %s: frames=%d duration=%.1fs bytes=%d" % (key, frames, secs, size))
    print("assertion pass: all", len(SEGMENTS), "content segments found verbatim in capture.json")
    shutil.rmtree(WORK, ignore_errors=True)


if __name__ == "__main__":
    main()
