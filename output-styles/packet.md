---
name: recognitio-packet
description: Shapes the recognitio review packet as the tiered section document the extractor writes. A format only. Every guarantee stays on the shipped scripts and the skill workflow.
force-for-plugin: true
---

# Recognitio review packet format

## Derivation

This style is a second spelling of the packet the extractor
writes. Its only source is the tier model, workflow,
completeness, trust, and stamping sections of
`.agents/skills/recognitio/SKILL.md`. It adds no instruction the
canonical text does not carry and moves no guarantee. Packet
enforcement stays where decision 4 of `docs/decisions.md` puts
it, in the shipped scripts and the skill workflow steps. When
this style is inert, the prose packet enforces every guarantee
unchanged.

## The packet shape

The packet is built in tiers and each tier is a named section of the packet.

```text
## T0 Triage
## T1 The change
## T2 Companions
## T3 History
## Re-review
## Budget and completeness
```

- T0 holds triage. It carries the pull request title, body, and spec references when the mode resolves them, the file list, the numstat summary, and the commit list for the range, so a reviewer sees why the change exists and what shape it has before its content.
- T1 holds the change itself. It carries the per file diffs with whole enclosing function context, so every edited line is read inside the function it lives in.
- T2 holds the companions. It carries call sites for the changed function names elsewhere in the repo, the imports of each changed file, definitions of the changed names outside the changed files, and the test files that mention the changed modules, all found by deterministic search and capped with the caps stated in the packet.
- T3 holds history. It carries a blame summary for the changed ranges in the most changed files, the recent evolution of up to three changed functions, and prior pull requests touching the most changed files when the GitHub CLI can name them.

## The contract

Read the manifest the script writes and check that its verified flag is true before anything else happens. A review is stamped only on a verified packet. Never present a partial packet as a complete one. Never let a review begin on a packet whose verified flag is false. When verification fails, stop and say what is missing in plain words, naming the files or hunks that disagree. A verified packet proves the packet is complete. It does not prove the change is correct or safe.
