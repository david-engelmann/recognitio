---
version: alpha
name: Product storefront
description: Design tokens and law for product storefront and landing pages of the Recognitio class, a Persuade surface held to evidence rules.
colors:
  ground: "#ffffff"
  panel: "#f6f8fa"
  ink-1: "#1f2328"
  ink-2: "#59636e"
  accent: "#D97757"
  hairline: "#d1d9e0"
typography:
  display:
    fontFamily: '"Mona Sans VF", -apple-system, BlinkMacSystemFont, "Segoe UI", "Noto Sans Backtick Fix", "Noto Sans", Helvetica, Arial, sans-serif, "Apple Color Emoji", "Segoe UI Emoji"'
    fontSize: "2rem"
  heading:
    fontFamily: '"Mona Sans VF", -apple-system, BlinkMacSystemFont, "Segoe UI", "Noto Sans Backtick Fix", "Noto Sans", Helvetica, Arial, sans-serif, "Apple Color Emoji", "Segoe UI Emoji"'
    fontSize: "1.5rem"
  body:
    fontFamily: '"Mona Sans VF", -apple-system, BlinkMacSystemFont, "Segoe UI", "Noto Sans Backtick Fix", "Noto Sans", Helvetica, Arial, sans-serif, "Apple Color Emoji", "Segoe UI Emoji"'
    fontSize: "1rem"
  caption:
    fontFamily: '"Mona Sans VF", -apple-system, BlinkMacSystemFont, "Segoe UI", "Noto Sans Backtick Fix", "Noto Sans", Helvetica, Arial, sans-serif, "Apple Color Emoji", "Segoe UI Emoji"'
    fontSize: "0.75rem"
rounded:
  ctl: "6px"
  panel: "6px"
  pill: "2em"
spacing:
  space-1: "4px"
  space-2: "8px"
  space-3: "12px"
  space-4: "16px"
  space-5: "24px"
  space-6: "32px"
  space-7: "48px"
  space-8: "64px"
  space-9: "96px"
components:
  hero:
    backgroundColor: "{colors.ground}"
    textColor: "{colors.ink-1}"
    padding: "{spacing.space-8}"
  panel:
    backgroundColor: "{colors.panel}"
    textColor: "{colors.ink-1}"
    rounded: "{rounded.panel}"
    padding: "{spacing.space-5}"
  primary-action:
    backgroundColor: "{colors.accent}"
    textColor: "{colors.ground}"
    rounded: "{rounded.ctl}"
    padding: "{spacing.space-3}"
  badge:
    backgroundColor: "{colors.panel}"
    textColor: "{colors.ink-2}"
    rounded: "{rounded.pill}"
    padding: "{spacing.space-1}"
  section-rule:
    backgroundColor: "{colors.hairline}"
    height: "1px"
---

# Product storefront

## Overview

This file is the design system for storefront and landing pages, the Recognitio class of surface. It is a Persuade surface in Impeccable's mode terms, a page whose job is to explain a real product and earn a real install or purchase. Persuasion here never outruns evidence. The page sells only what the product does, shows only output the product produced, and claims only numbers the product's own records carry.

This file stands adopted for the Recognitio repository page, and this adoption is its standing state. The token values in the front matter were extracted from the stylesheets the live page serves in the change that adopted the file, with the light theme carried as the canonical set, and they stand reconciled against the palette record under docs/brand in the repo. The spacing scale is the one part of the front matter that stands pre-filled as doctrine rather than extracted, carrying the house 4px scale the Layout section states. No placeholder values stand in this file. The instruction to replace placeholder values with extracted ones belongs to the unadopted template this file was adopted from, and it is spent.

The working method is the pinned v1 Taste machinery, scoped to this surface only. The kit deliberately pins the v1 classics, the design read, the DESIGN_VARIANCE, MOTION_INTENSITY, and VISUAL_DENSITY dials, the tell bans, and the pre-flight check, because v1 is the version whose text was read and verified during the kit's research. Upstream now ships tasteskill 2.5.0 under a different method, and the kit does not adopt it. Before building, the lane runs the v1 design read, reads the page type, the audience, the vibe words, and the references, and states a one line design read. The dials start at the trust first preset in the Layout section. At most one clarifying question is asked, and only when the read is genuinely ambiguous.

This file carries no colors.primary token, deliberately. The accent token carries the primary role, and the design linter's missing-primary warning on this file is expected and waived on the record in the kit's gates file. Agents must not auto-generate a primary token here.

## Colors

One accent, locked. The accent is chosen once for the page, stated here as the accent token, and used for the primary action and the primary reading path only. No second accent appears in chrome, controls, or decoration. All color and font choices route through the front matter tokens, never through raw values in the stylesheet.

Contrast meets 4.5 to 1 everywhere on the page apart from the one waived pairing recorded in this section, including placeholder text and button text. The primary action's label must pass AA against its own background, checked on the render, not assumed. One waiver stands on the record for this adoption. The primary action pairs the ground text color on the accent background at 3.12 to 1, below the AA floor stated above, and the pairing stands as shipped and as extracted, recolored in neither direction, because the accent is the shipped brand accent and the ground is its shipped label color. There is no purple to blue gradient anywhere on the page, and no gradient text. Structural elements are quiet, color carries meaning or identity, never decoration.

## Typography

One font system per page. If the product has an official design system or component package, the page installs and uses the real package. A hand rolled imitation of a known system is a defect, because it drifts from the thing it imitates and the drift reads as carelessness.

Line length for reading text sits between 65 and 75 characters. Display size is clamped, never above 6rem, and display letter spacing never goes below -0.04em. Headings state what the product is and does in plain words. A heading whose claim the product cannot back is rewritten until it can.

## Layout

The v1 Taste dials, as a working preset for a trust first product page.

- DESIGN_VARIANCE 3 to 4. Composed and predictable, with one or two deliberate breaks at most.
- MOTION_INTENSITY 2 to 3. Motion is present where the motion doctrine allows it and nowhere else.
- VISUAL_DENSITY 4 to 5. Enough air for a first time reader, enough substance to respect a technical one.

Spacing comes from the 4px based scale in the front matter, whose standing the Overview states once. The page never scrolls sideways. Overflow-x is clipped on html and body, image grids use minmax(0, 1fr) tracks, and nothing extends past the section edge at any audited width. Content is fully visible with scripting off.

## Elevation & Depth

Elevation is flat by default. Panels separate by surface step and hairline, not by shadow stacks. Glassmorphism is not a default material and appears, if at all, as one deliberate treatment with a stated reason on the record. No card sits inside a card. A depicted screen or capture sits on the page surface directly, framed by at most one hairline.

## Shapes

Radius values are extracted at adoption and then locked, one value for controls, one for panels, one pill value. After adoption, a radius that appears in the stylesheet but not in this file fails the drift check in the gates. Mixed radius dialects across one page are a defect of exactly the kind this file exists to prevent.

## Components

The hero states the product, what it does, and the one action the page asks for. A hero metric template used as decoration is banned, a big number with a small label and a gradient accent, unless the number is real, sourced from the product's records, and doing evidentiary work.

Badges follow the badge honesty rule. A badge's visible text, its alt text, and its rendered state must agree. A badge whose image reads failing while its alt text claims passing is a landing blocker, and the fix is to the badge or its source, never to the alt text alone. Badge state is verified on the render before landing.

Depicted output follows the depicted output rule. Every screenshot, capture, or animated demo on the page is backed by a capture record naming what produced it, when, and from which build. A mock that reads as real output is a defect. Where a capture cannot be produced, the page shows the real interface or nothing.

Calls to action say what happens next in plain words. One primary action per view. Secondary actions are quieter in surface and type, never in a second accent.

## Do's and Don'ts

Do.

- Run the design read and state it before building.
- Back every claim with the product's own records and every image with its capture record.
- Verify every badge, capture, and action on the render, at desktop and phone widths.
- Keep the page honest at the floor. No invented metric, testimonial, logo wall, or case study count, ever.

Don't.

- Invent social proof. No borrowed logos, no plausible user counts, no rounded up numbers.
- Decorate with status dots, middle dot meta strings, or emoji as icons.
- Add a theme system to a one off page without a reason on the record. One locked system per page.
- Let a landing ship on static renders alone. Phone width rendered verification is a landing requirement.

## Responsive Behavior

The page is audited at the same eight widths the fleet lint uses, from phone to wide desktop, and must hold at every one. Phone is a re-flow, never a squeeze. The hero, the primary action, and the first depicted output must all survive at 390 without clipping, overlap, or a sideways scroll.

Before landing, the page is rendered and inspected at phone width, and the interactive elements are exercised there. A storefront that was only ever seen at desktop width is unverified, whatever its screenshots say.

## Data & Motion

Storefront motion follows the house motion doctrine in the kit's `motion/MOTION.md`. The storefront is a Persuade surface, so the occasional and rare rows of the frequency table may use standard motion, and delight is allowed only on genuinely rare, low stakes moments. The bans still hold. Figures never animate, numbers never count up, and no metric tweens into existence. A number that animates into view is being performed, not reported, and this page reports.

Every number on the page traces to the product's records, the same evidence rule as the board, applied to marketing copy without exception. Where the product has no number, the page makes the claim in words the product can back, or makes no claim.

## Agent Prompt Guide

A lane briefed to build or review a storefront page works in this shape.

1. Role. You are building a Persuade surface for a real product, held to evidence rules.
2. Read. State the one line design read from the pinned v1 Taste machinery, page type, audience, vibe, references, before building. One clarifying question at most.
3. Dials. Set the v1 dials, DESIGN_VARIANCE, MOTION_INTENSITY, and VISUAL_DENSITY. Start at variance 3 to 4, motion 2 to 3, density 4 to 5. Deviations go on the record. The upstream tasteskill 2.5 method is not adopted.
4. Tokens. Build only from this file's tokens. On adoption, extract values from the live stylesheet, never invent them.
5. System. If an official design system or package exists for the product, install the real package. One system per project.
6. Claims. Every metric traces to the product's records. No invented proof of any kind.
7. Media. Every capture carries its capture record. Badges are checked on the render, text, alt, and state in agreement.
8. Motion. Apply the motion doctrine. Animate chrome, never figures.
9. Verify. Render and inspect at all audited widths, phone included, exercise the interactions, and run the gates before landing.
