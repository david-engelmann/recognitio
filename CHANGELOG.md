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

### Added

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
