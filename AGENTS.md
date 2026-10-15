# AGENTS.md

Operating notes for agents working in this repo. This file is the
single source of agent guidance here, and CLAUDE.md points at it.

## What this is

Recognitio is an agent skill that pulls the relevant changes out of
a pull request or a commit range and assembles them into a verified
review packet. The packet is called the pericope. The skill lives in
`skills/recognitio/` and its extractor is the script at
`skills/recognitio/scripts/extract.py`.

The skill assembles evidence and nothing more. Judgement about the
code belongs to the review skill that reads the packet downstream.

## The gate

Run the gate before every push and keep it green.

```bash
make check
python3 -m unittest discover -s tests
```

The first command is the full gate and the second is the narrow form
to use while working. The gate runs the extractor test suite, the
skill validator at `scripts/check_skill.py`, the copy bar scan at
`scripts/check_copy.py`, and an end to end extractor smoke that must
produce a verified manifest. CI runs the gate word for word. Green
local gates first, then merge. CI is a backstop, not a gate.

## Layout map

- `skills/recognitio/SKILL.md` holds the skill text an agent reads
  when the skill triggers.
- `skills/recognitio/scripts/extract.py` is the extractor. It is
  stdlib only and runs against a local clone.
- `tests/` holds the extractor suite. Fixture repositories are built
  in temporary directories by the tests themselves.
- `scripts/` holds the gate checks and the smoke script.
- `.github/` holds the CI workflow and the templates.

## Hard rules

1. Extraction comes from local git only. Never build a packet from
   a hosted API diff, because hosted diffs cap their file counts and
   drop oversized patches without a flag.
2. The manifest fails closed. A packet whose verified flag is false
   is not a packet, and nobody reviews it as if it were whole.
3. Stdlib only. The extractor and the gate scripts take no third
   party dependencies.
4. Every fix ships with a test that fails when the fix is reverted.
   A test that cannot fail for a real reason is not a test.
5. The skill is never named `code-review`. That name would shadow
   the bundled command in Claude Code and muddy the namespace.
6. Public prose follows the copy bar. No em dashes, no colons and
   no semicolons in prose sentences. The gate enforces the bar.

## Conventions

- The default branch is `dev`. Branch off `dev` under a name of the
  form `kind/slug` and open the pull request against `dev`.
- The `main` branch is the release branch. It moves only through
  promotion pull requests from `dev`, and release tags are cut
  from `main` by David alone.
- Pull request titles follow Conventional Commits and become the
  squash commit title. Merges are squash only.
- Every commit carries a `Signed-off-by` trailer with the identity
  of David Engelmann. Sign commits with `git commit -s` and let the
  DCO job in CI check the trailer.
- Changelog entries go at the end of the `[Unreleased]` section of
  CHANGELOG.md. A released section is never edited after its tag.
- Update this file in the same change that makes part of it wrong.

## Docs update map

CI cannot tell whether the docs are current, so reviewers check
this map instead.

- Extractor behaviour changes update SKILL.md and CHANGELOG.md in
  the same pull request.
- Tier or manifest changes also update the tier model section of
  README.md in the same pull request.
- A change to the description field in SKILL.md is a spec change,
  and the pull request body says so and says why.
- Gate changes update this file and the CI workflow together.

## Current state

Written on 2026-10-15. The first version of the skill is built and
landing on `dev`, with the extractor, the four tier model and the
fail closed manifest in place. No release has been tagged yet.
