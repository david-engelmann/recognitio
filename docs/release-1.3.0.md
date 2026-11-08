[Back to the documentation index](README.md)

# The 1.3.0 release

This file holds the release notes and the tag checklist for
recognitio 1.3.0, the first release of the skill and its plugin
packaging. No tag candidate stands named on the face of this
file while the tag stays held. The candidate is restated here
to the final landing head at the close of the perfection
programme, in the last step before the owner cuts the tag,
and the first item of the checklist below holds that step
open until then. These notes describe the tree the
storefront landing carried onto main. That landing head is
`357ba2d43d74f295c8e1953fe3dadd3406c2eb63` and its tree is
`5bd54e64ceec144b9408e9ee5a61730d735abce4`. The heads this
file named in earlier rounds were the landing heads of
their own restatements, and each one stopped being the head
of main at the next landing, so no head named here is
stated in the present tense as the head of main. No tag
has been cut, and the tag itself stays held. Cutting the tag
is the owner's act alone, and this file records the notes the
release carries and the checklist that act follows.

## Release notes

- The recognitio skill in its first working version. The
  bundled extractor pulls the relevant changes out of a pull
  request, a commit range or a single commit from the local
  clone and assembles them into a review packet across four
  tiers, with a manifest that records every changed file and
  hunk and an independent recount that must agree with the
  manifest before the packet is called verified.
- A packet check script that validates a packet directory
  before a review is stamped on it, a findings file for
  re-review, named placeholders for binary and generated and
  lockfile entries, and a tier selector and a token budget
  that shape a run without dropping its verification.
- Plugin packaging for the home platform, with a plugin
  manifest and a marketplace listing, a reviewer persona as
  the session main thread, a packet output style, a headless
  review shape, a review fan out workflow with a shipped
  proof run, and the Build 7 spawn gate mod, packaged both
  inside the main plugin and as the recognitio-mod entry on
  its own.
- The Agent Plugins 1.0.0 portable package with its closed
  schema manifest and a byte identical copy of the canonical
  skill, with the native shapes riding beside it at the repo
  root as per platform extensions.
- Platform builds that restate the packet discipline in the
  surface each platform reads, covering Codex review rules
  and the Codex plugin, the Cursor plugin and its Bugbot
  rules, the CodeRabbit guidelines, the Antigravity plugin
  alteration, the Copilot SDK agent build, the Kimi managed
  plugin, the ZCode plugin, the Devin playbook and
  coordinator build, the Qwen Code conditional presence and
  the Comate adaptation.
- A paired eval layer under evals, with planted defect tasks
  that record what a reviewer finds from the packet against
  what the same reviewer finds from the raw diff, a trigger
  set for the skill description, and a corpus index that maps
  the audit incidents to the tests that cover them.
- A gate that runs the whole repo on every change, with the
  extractor suite, the skill validator, the version
  coherence check, the copy bar scan, the eval integrity
  check, and one check per platform build, ending on an end
  to end extractor smoke that must produce a verified
  manifest.
- A public storefront whose hero is a filmed Claude Code
  session running the spawn gate deny then proceed arc over
  a real range, with a proof strip of real frames from
  Claude Code and Codex and Cursor and Qwen sessions over
  the same range, each frame traceable to its capture
  record.

## The tag checklist

- [ ] The candidate head is restated on the face of this
  file to the landing head, and the landing head is the
  head the gate ran on.
- [ ] The full gate passes on the candidate head through
  the make check command, with its exit code captured.
- [ ] The three reviews of the checkpoint rule stand
  complete on the landing change, with every finding fixed
  or dispositioned in the open.
- [ ] Every version string in the tree reads 1.3.0, across
  the extractor, the plugin manifests, the marketplace
  listings and the portable package, and the changelog
  carries the release under its 1.3.0 heading.
- [ ] The README page weight ledger stands under its
  ceiling on the candidate head, with the ledger stated in
  the gate test in the open.
- [ ] The pushed tree is verified blob for blob against the
  gated local tree, with exec modes restored on every
  script the push carries.
- [ ] The owner cuts the tag from main and names it v1.3.0,
  because release tags are the owner's act alone.
- [ ] The release notes above are pasted into the release
  the tag creates, with no claim added that this file does
  not carry.

## Navigation

- [Documentation index](README.md)
- [Decisions](decisions.md)
- [Principles](principles.md)
