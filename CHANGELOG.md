# Changelog

All notable changes to recognitio are recorded in this file.

The format follows Keep a Changelog and the project versions follow
Semantic Versioning.

## [Unreleased]

### Added

- The recognitio skill in its first working version. The bundled
  extractor pulls the relevant changes out of a pull request, a
  commit range or a single commit from the local clone and assembles
  them into a review packet across four tiers. Triage comes first,
  then the change itself with whole enclosing function context, then
  companion call sites and test files, then history. A manifest
  records every changed file and hunk, and an independent recount
  must agree with the manifest before the packet is called verified.
- The pull request title, body and spec references in the triage
  tier, and the changed file list beside the numstat summary.
- Imports of the changed files and definitions of the changed names
  in the companion tier.
- Prior pull requests touching the same files in the history tier,
  gathered with the GitHub CLI when it is available and named as
  unavailable when it is not.
- A tier selector that chooses which companion and history tiers a
  run builds, separate from the budget mechanism.
- A findings file for re-review. Each prior finding is marked
  addressed or unaddressed by whether its anchored lines changed.
- Named placeholders for binary files and for files detected as
  generated or as lockfiles, with every placeholder listed in the
  packet header and counted in full in the manifest.
- The packet check script, which validates a packet directory
  before a review is stamped on it.
- The manifest now records the producing command, the extractor
  version and a creation time.
- A decisions file that records where the design departs from the
  research sketch and why.
- Tests for the gate scripts themselves, for pull request mode with
  a stand in GitHub CLI, and for all three budget outcomes.

### Fixed

- Paths that git quotes no longer drop out of the packet. Path data
  moves through NUL delimited output, and every git invocation runs
  with its output format pinned, so ambient configuration in the
  clone or in a global config file cannot reshape the diff.
- Binary files and non UTF-8 content no longer crash the extractor.
- A text file the tree marks binary through its attributes file is
  counted and shown as text, and named in the receipt.
- Pull request mode no longer falls back to a same named local
  branch. It fails loudly when the refs are not in the clone.
- Shallow clones are refused with a clear message.
- The completeness recount covers added and deleted lines and old
  paths as well as files, statuses and hunks.
- The token budget accounts for the whole packet, and the receipt
  reports tokens per tier, files per tier and what was cut.
- A failed run no longer leaves a previous verified packet standing
  in the output directory.
- A root commit no longer records the empty tree as its merge base.
- Call sites in files whose path contains a colon are found again.
- Packet text preserves the bytes of the change, CRLF endings
  included.
- An unrelated since ref now produces an explicitly empty and
  scoped re-review section instead of a confident one, and a since
  ref on its own is no longer accepted as a mode.
- The DCO job exempts dependabot by actor and requires the exact
  sign-off identity on human commits, and the copy gate now scans
  every public prose surface in the repo.
- A second hardening round from review. The DCO job now reads the
  trailer block of a commit message instead of the whole message,
  the copy gate stops exempting punctuation that trails a link, and
  the packet check rejects an empty packet file and a manifest that
  is not a JSON object. The extractor pins the grep column and the
  inter hunk context settings, scrubs git location variables from
  the environment of its child processes and gives every child
  process a timeout. Deleted files are read through their entry
  path, so a deleted binary or generated file keeps its placeholder
  and its receipt line. Findings accounting keys its ranges by the
  path a finding was anchored under, ignores pure insertions, and
  the re-review section gates on a shared merge base, so a rebased
  head is re-reviewed instead of skipped.
- Replace refs can no longer swap the content under review. Every
  git invocation refuses replace objects, the child environment
  pins the same refusal, and the packet check reads the head under
  the same discipline.
- The line recount parses hunks structurally, so a content line
  whose text begins with two plus signs or two minus signs counts
  as content instead of being skipped as a diff header. Ordinary
  changes carrying SQL comments or TOML delimiters verify again.
- Attribute marked files are measured from numstat read with the
  text flag and cross checked against the diff body like every
  other text file. Their counts can no longer rest on one counter.
- Per file re-measurement diffs under literal pathspecs and under
  both names of a rename. A renamed attribute marked file is
  measured as its real delta, and a file named with glob
  characters shows its own diff rather than a neighbour file's.
- The range diff and the diff stat fallback in the re-review
  section carry the same pins as every other diff, and the range
  diff reads attributes from the empty tree, so a text conversion
  driver in the reviewed tree cannot rewrite the re-review. The
  range diff also pairs commits at the maximum creation factor,
  because a small commit pairs with nothing at the default factor
  and its inner diff would vanish from the re-review.
- The companion searches read attribute marked files as text. A
  tree that marks its sources binary can no longer hide its own
  call sites and leave the packet reporting that none exist.
- GitHub CLI failures of every shape now end in the failure
  receipt and the exit code the contract promises. A missing CLI,
  an unparseable answer and a wrongly shaped one no longer escape
  as tracebacks.
- A run rejected while its arguments are checked clears the output
  directory and leaves the failure receipt like any other failed
  run, so the standing promise about stale packets holds without
  qualification.
- A generated file marker withholds a diff only when the marker
  already stood at the base revision. A marker that arrives in
  the change is flagged in the packet header and the change is
  shown in full.
- The pull request body, the numstat block and the commit list
  are fenced with a fence longer than any run of backticks inside
  them. Reviewed text can no longer break out of its fence and
  forge a packet section.
- The manifest records the section headings it emitted and the
  packet check verifies those sections are present and filled,
  so a thin packet cannot wear a full packet's manifest. The
  headings are counted outside the packet's fences on both
  sides, so quoted text from the change under review cannot
  stand in for a section, and a manifest that records no
  sections fails the check outright.
- Findings accounting reads the head tree once instead of once
  per finding, is capped at one hundred findings with the cap
  stated in the section, and names an empty findings file in the
  re-review section instead of letting it vanish.
- The exclusion receipt holds one entry per file. An attribute
  marked lockfile is receipted once, as the lockfile it is shown
  as, and never also as a file shown as text.
- The prior pull request lookup states the window it covers in
  the packet and in the docs, and the receipt prose defines what
  the files per tier counts count.
- The copy gate scans the issue template config file and the
  comment prose of the workflow, the dependabot config, the
  Makefile and the gitignore file, so the coverage the gate
  claims is the coverage it has.
- The budget decision measures each candidate packet by
  assembling it, the same fixed point the shipped packet is
  measured at. A fixed allowance for the completeness section
  undercounted it whenever the section grew, and packets the
  budget accepted could land over the budget.
- The pipeline is split into named stage functions, and the
  packet write fails in the same clean voice as every other run
  failure instead of escaping as a traceback.
