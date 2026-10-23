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
skill validator at `scripts/check_skill.py`, the version coherence
check at `scripts/check_version.py`, the copy bar scan at
`scripts/check_copy.py`, the eval integrity check at
`scripts/check_evals.py`, and an end to end extractor smoke that must
produce a verified manifest. The eval integrity check reads the
checksum record at `evals/checksums.json` over the eval artefacts,
the results file, the per pass notes and the corpus index, and
fails on the first file whose bytes moved. The record loads
through a strict reader that refuses a repeated key, and its keys
use the forward slash spelling on every host. The check also
re-derives the task-06 scores from its transcripts and its planted
grading rule, compares each task sources file against the source
anchor record at `evals/source-anchors.json`, and compares each
corpus section against the coverage record at
`evals/corpus-coverage.json`. The anchor and coverage records stand
apart from the checksum refresh. A deliberate eval update moves
them first with the anchor and coverage write flags of the gate
script, each as its own committed step, and then refreshes the
checksum record by running
`python3 scripts/check_evals.py --write-checksums` and committing
the record beside the artefacts it covers. The checksum refresh
refuses to run while an anchor or the coverage is stale. CI runs the gate word for word and
adds one job with no local step. The DCO job checks the Signed-off-by
trailer on pull request commits, and a green local run says nothing
about it. Green local gates first, then push. CI is a backstop,
not a gate.

## Layout map

- `skills/recognitio/SKILL.md` holds the skill text an agent reads
  when the skill triggers.
- `skills/recognitio/scripts/extract.py` is the extractor. It is
  stdlib only and runs against a local clone.
- `tests/` holds the extractor suite and the gate script suite.
  Fixture repositories are built in temporary directories by the
  tests themselves.
- `scripts/` holds the gate checks and the smoke script.
  `scripts/check_packet.py` validates a packet directory before a
  review is stamped on it.
- `docs/decisions.md` records the design decisions that depart from
  the research sketch, with the reason for each one.
- `docs/reviews/` holds review reports written from the template
  in `REVIEW.md`, with their findings disposition counts.
- `evals/` holds the paired eval tasks, the trigger set, the
  corpus index and their recorded results.
- `.claude-plugin/` holds the plugin manifest and the marketplace
  listing for the skill.
- `REVIEW.md` records the review workflow shape for this repo.
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

- The default working branch is `main`. Review work branches off
  `main` under a name of the form `kind/slug`, and the reviewed
  change lands on `main` by direct push of its commits. Pull
  requests are the exception for structurally large changes that
  want a public review trail, not the cadence.
- Release tags are cut from `main` by David alone.
- The `dev` branch is vestigial. It carried the work until the
  promotion of October 2026 and no work branches from it or
  targets it any more.
- Commit titles follow Conventional Commits on every commit pushed
  to `main`, including the machine-made mode-only follow-ups the
  Data API path needs. Content commits take `fix:`, `feat:`,
  `docs:` or `test:` as fits, post-gate repair commits take `fix:`,
  and mode-only follow-ups take `chore:`. One round of review
  fixes lands as one commit on `main`.
- Every human commit carries a `Signed-off-by` trailer with the
  exact identity of David Engelmann. Sign commits with
  `git commit -s`. The CI DCO job enforces the trailer on pull
  request commits, and direct pushes to `main` carry the trailer
  because the coordinator checks every trailer before the push.
  Dependabot is exempt by actor, because its commits
  are machine made and cannot carry a sign-off, and the exemption
  lives in the workflow file next to the check. The exemption keys
  on the actor and not on the author of the commits. A re-run or a
  reopen that a person triggers on a dependabot pull request names
  that person as the actor, so the job runs on those events and
  fails the machine made commits it was built to skip. That edge
  is known and accepted.
- Changelog entries go at the end of the `[Unreleased]` section of
  CHANGELOG.md. A released section is never edited after its tag.
- Update this file in the same change that makes part of it wrong.

## Docs update map

CI cannot tell whether the docs are current, so reviewers check
this map instead.

- Extractor behaviour changes update SKILL.md and CHANGELOG.md in
  the same change.
- Tier or manifest changes also update the tier model section of
  README.md in the same change.
- A change to the description field in SKILL.md is a spec change,
  and the change notes say so and say why.
- Gate changes update this file and the CI workflow together.
- A version string change moves every surface that carries one in
  the same change, and the gate checks that they agree.
- A change to REVIEW.md updates CHANGELOG.md in the same change.
- A change under evals/ updates the recorded results it touches
  in the same change, and a change to the eval method also
  updates the runner note in evals/README.md and CHANGELOG.md in
  the same change. Packets saved as fixtures are regenerated
  with the shipped extractor and carry verified manifests.
- A change to the plugin manifest or the marketplace listing
  beyond a version string updates the install section of
  README.md and CHANGELOG.md in the same change, and the
  gate tests that pin the manifest shape move with it.

## Current state

Written on 2026-10-15 and updated on 2026-10-23. The first version
of the skill is built and landed on `main`, with the extractor, the
four tier model and the fail closed manifest in place. The first
perfection cycle hardened the extractor against ambient git
configuration, grew the tier content the design called for, and put
the gate scripts under test. The second cycle pinned object
identity against replace refs, rebuilt the recount the first cycle
added so ordinary content cannot fail or slip it, and closed the
failure paths at the argument checking boundary. The round 1 pass
then closed the crafted filename and never existed findings and
binary transition findings, banned marks left the generated
packet prose, and the plugin packaging and the eval layer landed.
The round 2 pass then escaped the cap notes, rebuilt the companion
search on its NUL delimited records and one bulk search, deduped
the findings accounting, hardened the version gate against wrong
typed JSON, and made the copy fence discover its surfaces by rule.
The round 3 pass then deduped the test files section by line,
brought the bulk matcher under the same boundary rule as the per
term search, restricted the version shape to ASCII digits, made
the YAML half of the copy fence discover by the same rule as the
Markdown half with one shared exclusion predicate, and settled the
skill description on a held out trigger run. The round 4 pass
then searched a renamed module under its old stem as well as
its new one, exempted YAML structure from the copy fence while
keeping prose values under it, normalised a leading ./ in
findings paths, completed the corpus index with its round 2
section, and gave decision 3 an explicit trigger for a runnable
incident suite. The round 6 pass then stopped a copied entry
from writing re-review ranges under its source path, set the
marketplace entry to strict so the plugin loads through the
marketplace route beside a gate check on the manifest pair,
read YAML structure in the copy fence by structure rather
than by key pattern, flagged instruction bearing files in the
packet, completed findings path normalisation across its
sibling spellings, guarded the skill file size in the gate,
and added a replay eval task drawn from a real merged pull
request with verbatim transcripts. The round 7 pass then
aligned the manifest conflict gate with the host on a
missing strict key and on component fields declared under
the experimental object of an entry, flagged the path
specific Copilot instructions files and the Claude rules
files in the packet, guarded the skill file size in bytes
as well as characters, rested the re-review verdict on the
content change of the anchored lines with line endings
normalised away, and lifted the stateful YAML reader of
the copy fence into named helpers under the recorded
function ceiling. The round 8 pass then pinned the eval
artefacts under a checksum record with a totals check on
the recorded results and a rebuild of every task diff and
manifest from its sources, and turned the corpus index
discipline into a gate check that fails when a cited test
name leaves the suite. The round 9 pass then re-derived the
task-06 scores from its transcripts and its planted grading
rule, anchored each task sources file under a digest record the
checksum refresh cannot move, refused a repeated key in every
record the gate trusts, spelled record keys with forward
slashes on every host, brought the corpus index under the
checksum record with a per section coverage floor, completed
the round 8 corpus section, and pinned the shipped help output
against banned marks. The owner dropped
the branch ceremony on 2026-10-22 and `main` became the working
branch the same evening. No release has been tagged yet.
