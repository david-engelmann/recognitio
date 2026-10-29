[Back to the documentation index](README.md)

# The Claude plugin directory submission pack

## At a glance

**What ships**

This pack and nothing else. It holds the filing route for the
Anthropic plugin directory, the requirement set read from the
primary Anthropic pages, and an evidence check of every
requirement against the shipped tree, so the filing can go
ahead on the decision of the owner without further research.

**What was proven**

Every requirement the primary pages state was checked against
the shipped manifests and files on 2026-10-27, apart from the
size limits item, which was restated on 2026-10-28 against the
tree that then held 220 files. The gate at
scripts/check_submissions.py pins the facts the check rests
on, so drift in a manifest or in this pack fails the gate.
The check is a tree check against the primary text. The one
tool run the docs describe stands owed, as the filing steps
record, so this pack is evidence checked and not tool
verified.

**What is unverified**

The portal stands behind a claude.ai sign in, so its form
fields and the name availability check are unverified here.
The local validator run the docs describe is still owed,
because no Claude Code client stands on this box.

## Summary

Nothing in this pack has been submitted. The pack is written
against version 1.3.0 of recognitio. Requirements were read
from the primary sources named in this pack on 2026-10-27.
Three different listings are easy to confuse, and this pack
keeps them apart. The directory on claude.ai takes open
submissions through its portal and is the route this pack
prepares. The official marketplace takes no submissions
through that portal, and the primary pages name no open route
into it for an unaffiliated author. The marketplace file this
repo already ships needs no submission at all, because adding
the repo as a marketplace is already a working install route
with no Anthropic involvement.

## The route

Submission is open to anyone on a paid Claude plan, with no
partner program to join first. The portal stands at
claude.ai/directory/manage, where the submitter creates a
submission for one plugin folder at a time and chooses the
plugin bundle kind. Skills are not a submission kind on their
own, so the skill rides inside the bundle, which is the shape
recognitio already ships. The GitHub account of the submitter
must be connected on claude.ai in the organization the
submission comes from, and the portal checks that the account
can push to the repo before it accepts a submission. The repo
may stay private while the submission is prepared, and it
must be public before the listing goes live. Recognitio is
already public. Plan eligibility is Pro, Max, Team, or
Enterprise, and free accounts cannot submit. On Pro and Max
plans the account holder submits with no role check. On Team
plans an owner submits. On Enterprise plans an owner submits,
and an Enterprise owner can also grant the directory
permission to other members through a custom role, who may
then submit in the name of the organization. The listing
belongs to the organization that submits it.

## What the listing needs

The manifest at .claude-plugin/plugin.json has one required
key, the name, which must be lowercase kebab-case, must not
be a reserved word, and must not present the plugin as
official. The directory adds its own checks on top of the
manifest. A README of at least 40 words outside code blocks
must sit in the plugin folder, because the directory shows
that README as the listing description, and it must describe
everything the plugin runs, sends, or fetches. A LICENSE file
in the folder or a license value in the manifest must stand,
or validation blocks. Every component path must stay inside
the plugin folder with a relative path, and every skill,
agent, and command file must carry valid frontmatter with a
description as a single text value. Real credentials belong
nowhere in the folder. Package launchers must pin exact
versions. Every file in the folder must stay under 5 MiB,
and the repo must stay under the stated archive and unpacked
size limits. Five listing fields live in the manifest only,
the icon as a path to an image inside the plugin and four
URLs for documentation, support, privacy policy, and terms
of service, and none of the five is required by the manifest
reference. The directory policy adds obligations the
automated checks do not cover, among them verified contact
information and support channels, at least three working
examples of use, and a privacy policy link when the software
collects user data or connects to a remote service.

## Review and validation

Each submitted version passes automated validation and a
security scan, and a person reviews a new listing before it
goes live. Findings carry four severities. A blocking finding
stops the submission until it is fixed and revalidated. A
policy hold lets the submission proceed while a reviewer
reads the held version. A warning may stand. A note is
information only. The docs describe a local validator a
submitter can run first, and the portal runs further checks
the local command does not, including the README, the
license, and whether the name is taken. No primary page
states a review time, and the status page repeats that the
time is not fixed. After the first listing, updates need no
resubmission, because the directory picks up new commits from
the tracked branch, scans each one, and serves it once
published. Under the default setting the submitter selects
Publish on a passing version and an Anthropic reviewer
publishes it.

## The evidence check

**Met, the name.** Recognitio is lowercase kebab-case, well
under the length cap, built on the name of the project, and
no reserved word or Anthropic name stands in it.

**Met, the manifest fields.** The shipped manifest carries
the display name, the version, the description, an author
object with a name and an email, the license value MIT, the
homepage and repository values, the keyword set, and the icon
path pointing at the 512 pixel PNG inside the repo. Absence
of the author would only warn. The license stands in both
forms the checklist accepts, the value in the manifest and
the file at the root, and absence in both forms at once is
what blocks.

**Met, the marketplace file.** The shipped file carries the
required name, owner, and plugins fields, with two entries.
The recognitio entry matches the manifest name exactly,
takes the root as its source, and sets strict mode on. The
recognitio-mod entry names the spawn gate mod on its own,
takes the plugin folder under plugins as its source, and
sets strict mode on. That file already publishes the self
hosted route today.

**Met, the license and the README.** A LICENSE file stands
at the repo root, which is the plugin folder this submission
would name. The root README runs to thousands of words, far
past the 40 word floor, and it documents what the tool does,
how it is installed, and how a review runs from a packet.

**Met, the size limits.** The repo holds 220 files and a
few megabytes in total, as restated on 2026-10-28 against
the tree that then held that count. Its largest file is the
demo recording at 646,314 bytes, well under the 5 MiB file
limit. The file count also holds under the cap the
checklist holds for a reviewer, at 220 files against a cap
of 512 files. Its largest file that is not an image or a
font is tests/test_gate_scripts.py at 238,788 bytes, under
the 256 KiB cap of 262,144 bytes the same checklist holds
for such files. Its tracked extensions run to .gif and .js
and .json and .md and .mdc and .patch and .png and .py and
.svg and .ts and .yaml and .yml beside five entries with
no extension, of which one is the Claude skill symlink and
four are regular files, so no file falls outside the
allowed file type list on its extension.

**Open, the worked examples.** The directory policy asks for
at least three working examples that show the core
functionality. The README carries one worked example in full
and a quickstart beside it, and a count of three examples in
the form the policy names is not established on the page the
directory would show. Adding two more worked examples to the
README is a small pre-filing task, and this pack records it
as open rather than rounding the quickstart up to an example.

**Met, the hooks disclosure.** The hooks folder stands at
the repo root beside the manifest, and its wiring loads with
the plugin even though the manifest names no hooks field.
The checklist treats that omission as a warning. The sharper
point is disclosure, and it is met. The checklist asks the
README to describe everything the plugin runs, sends, or
fetches, and the README the directory would show names the
hooks module in its install section and states what the mod
does while the plugin is enabled, that it checks every
agent spawn in the session against the review packet
manifest and denies any spawn whose packet is missing or
unverified, and that it does nothing when no packet
directory is configured. The full contract stands in the mod brief, and
the marketplace listing offers the mod as its own entry
beside the plugin entry.

**Named, the symlink in the folder.** A symlink stands at
.claude/skills/recognitio and points at the canonical skill.
The plugin loads its skill from the real directory the
manifest names, so the symlink is not a file the plugin
loads. The checklist row settles the shape. A symlink
standing in for a file the plugin loads blocks, and a
symlink elsewhere warns. This one loads nothing, so the
expected outcome is a warning, and the portal run is where
it would be recorded.

**Open by choice, the listing URLs.** The documentation and
support URL fields stand unset in the manifest. Neither is
required, and the support value is the cleanest evidence for
the policy requirement of a support channel. Setting both is
a small manifest change the owner can make before filing,
and this pack records the choice instead of making it.

**Met, the component paths and the folder bars.** The four
component paths in the shipped manifest, the icon and the
agents entry and the skills entry and the outputStyles
entry, all resolve inside the repo root on relative paths.
The three component files carry frontmatter descriptions
as single text values, the skill at 548 characters and the
reviewer agent at 122 characters and the output style at
172 characters. A credential pattern scan over all 220
tracked files, for private key headers and AWS key shapes
and GitHub token shapes, returned zero hits, so no real
credential stands in the folder. No package.json ships
anywhere in the tree and the shipped manifest carries no
launcher field, so the launcher pinning row has nothing to
engage. The terms of service URL field stands absent from
the shipped manifest in the same unset state as the
documentation and support fields the listing URLs item
above records.

**Open, the verified contact information.** The directory
policy asks for verified contact information, and the
shipped manifest carries an author name and the email
81196676+david-engelmann@users.noreply.github.com that the
verification would attach to. Verification itself is an
account act at filing that no tree check can perform, so
this pack records the obligation as open and unverified
here.

**Open, the privacy determination.** No primary source makes
a privacy policy link turn on which component types a plugin
ships. The trigger is functional. Software that collects
user data or connects to a remote service must provide one.
The facts of this plugin are plain. Its extractor reads a
local clone and sends nothing anywhere. Its history tier
gathers prior pull requests through the GitHub CLI of the
reader when that tool is available, which is a connection to
GitHub under the credentials of the reader. Whether that
reads as connecting to a remote service under the policy is
the attestation of the submitter at filing, and this pack
records the facts and leaves the call there.

## Filing steps

1. The owner confirms a paid Claude plan on the account that
   will submit, in the organization that will hold the
   listing.
2. The owner connects the GitHub account on claude.ai and
   confirms it can push to this repo.
3. A validator run on the plugin folder and on the repo
   stands as the last local check, on a box with the Claude
   Code client installed.
4. The owner opens claude.ai/directory/manage, starts a
   submission, and chooses the plugin bundle kind for the
   repo root folder.
5. The owner runs the portal validation and answers every
   blocking finding, then submits.
6. The owner watches the status page, answers any request
   for changes, and selects Publish when a version passes.
7. Later versions then flow from the tracked branch with no
   resubmission, each scanned before it is served.

## What remains David's act

The whole filing. Holding the paid plan, connecting the
GitHub account, creating and submitting the submission in
the portal, and selecting Publish are account acts no agent
can perform in his place. Submitting also makes the
warranties the directory terms state, that the submitter
holds the rights to the software and that the information
given is accurate, and those warranties are his to make. The
privacy determination above is his attestation for the same
reason. Answering a reviewer, appealing a decision, and
withdrawing or relisting all stand in the portal under his
account as well.

## What is unverified

The field labels inside the portal form are unverified,
because the portal stands behind a sign in. Whether the name
recognitio is already taken in the directory is a portal
stage check and is unverified here. Whether the testing
account clause of the policy is enforced for a local plugin
with no account gated service is unverified. The per surface
component matrix for a directory listing was not read in
this pass, so no claim stands here about which components
load in which app beyond the one listing fact above.

## Sources

- Publish to the directory at https://claude.com/docs/directory/publish
- Submit your plugin at https://claude.com/docs/plugins/submit
- The pre-submission checklist at https://claude.com/docs/plugins/pre-submission-checklist
- Submission status at https://claude.com/docs/directory/submission-status
- The manifest reference at https://code.claude.com/docs/en/plugins/manifest-reference
- The marketplace reference at https://code.claude.com/docs/en/plugins/marketplace-reference
- Anthropic marketplaces at https://code.claude.com/docs/en/plugins/anthropic-marketplaces
- The directory policy at https://support.claude.com/en/articles/13145358-anthropic-software-directory-policy
- The directory terms at https://support.claude.com/en/articles/13145338-anthropic-software-directory-terms
- The community marketplace mirror at https://github.com/anthropics/claude-plugins-community

## Navigation

- [Documentation index](README.md)
- [Decisions](decisions.md)
- [Principles](principles.md)
