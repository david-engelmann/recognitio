# Documentation

New to this repo. Start with the principles page for what a
review packet owes its reader, then take the headless runbook
for how an unattended review runs, and keep the decision record
open while you read any brief. Every brief below states one
platform build, and the record behind every brief stands in the
decisions entry in the records section. The filed records at
the end of this page list every review report and the demo
capture record, so no document in this set stands unlisted.

## Start here

- [Principles](principles.md) (current) states the claims a review packet
  owes its reader, each one paired with the failure in this
  project record that produced it.
- [The headless review shape](headless-review.md) (landed) is the runbook
  for an unattended review, with its invocation, its findings
  schema and the fail closed contract the gate checks.
- [The reviewer persona](reviewer-persona.md) (landed) describes the
  Build 5 plugin agent that answers in the main thread of a
  session, with its host rules, its frontmatter panel and its
  limits.

## The platform builds

- [The Build 7 mod](mod-build7.md) (landed) gates the reviewer fan out
  at spawn time on the verified flag in the packet manifest.
- [The Build 8 portable package](agent-plugins-brief.md) (landed)
  carries the portable core under a closed schema manifest
  while the native shapes ride beside it at the repo root.
- [The Build 9 Codex review rules package](codex-review-brief.md) (landed)
  writes the packet discipline as derivation noted rules for
  Codex review.
- [The Build 10 Cursor plugin](cursor-plugin-brief.md) (landed) ships
  the skill as a real directory copy with one rule file, plus
  the Bugbot rules and their repo config.
- [The Build 11 CodeRabbit guidelines build](coderabbit-review-brief.md) (landed)
  writes the packet discipline as derivation noted guidelines
  that pair with the packet and never replace it.
- [The Build 12 Antigravity plugin alteration](antigravity-plugin-brief.md) (landed)
  records the plugin format, the dated sunset evidence, the
  version pin and the PreToolUse hook decisions.
- [The Build 13 Copilot SDK agent build](copilot-sdk-brief.md) (landed)
  writes the packet discipline as derivation noted rules for a
  review advisory layer beside the packet.
- [The Build 14 Kimi managed plugin](kimi-plugin-brief.md) (landed)
  states the managed plugin contract as derivation noted rules
  covering its manifest field, its hook events and its size
  limits.
- [The Build 15 Qwen Code marketplace presence](qwen-code-brief.md) (conditional)
  is a conditional draft in which no listing file ships and
  nothing is presented as published.
- [The ZCode plugin build](zcode-plugin-brief.md) (landed) records the
  Build 16 native plugin, its marketplace distribution and
  version bump rule, and the portable fields that lose effect
  there.
- [The Build 17 Devin playbook and coordinator build](devin-playbook-brief.md) (landed)
  writes the packet discipline as derivation noted rules for
  the Devin review surface and its coordinator surfaces.

## The release

- [Recognitio 1.3.0 release draft](release-1.3.0.md) (draft) carries the
  notes for the first tagged release, its highlights graphic and the
  ordered tag checklist its owner works through to ship it.

## The records

- [Decisions](decisions.md) (living) is the numbered record of the
  design decisions that depart from the research sketch this
  project grew from, with the reason for each one and dated
  notes where later rounds amended an entry.

## The filed records

- [The demo capture record](images/capture-record.md) (record) states how
  the hero recording was captured from one real Cursor agent
  session, with its prompt, its range and its disclosed
  shaping choice.
- [The round 4 fix review](reviews/round4-fix-review.md) (record) closes the
  round 4 findings, covering the renamed module search, the
  YAML fence scope and the findings path spelling.
- [The round 6 fix review](reviews/round6-fix-review.md) (record) closes the
  round 6 findings, covering copied entry ranges, the strict
  marketplace entry and the copy fence structure reading.
- [The round 7 fix review](reviews/round7-fix-review.md) (record) closes the
  round 7 findings, covering the manifest conflict gate, the
  instruction file flags and the skill size guard in bytes.
- [The round 8 fix review](reviews/round8-fix-review.md) (record) closes the
  round 8 findings, landing the eval integrity gate with its
  checksum record over the eval artefacts.
- [The round 9 fix review](reviews/round9-fix-review.md) (record) closes the
  round 9 findings, hardening the eval integrity gate and
  completing the corpus index for round 8.
- [The round 11 fix review](reviews/round11-fix-review.md) (record) closes the
  round 11 findings and lands Build 1, the skill frontmatter
  control panel.
- [The round 12 fix review](reviews/round12-fix-review.md) (record) closes the
  round 12 findings and lands Build 2, the canonical skill
  location.
- [The round 13 fix review](reviews/round13-fix-review.md) (record) closes the
  round 13 findings and lands Build 3, the packet output
  style.
- [The round 14 fix review](reviews/round14-fix-review.md) (record) closes the
  round 14 findings and lands Build 4, the headless print
  mode CI shape.
