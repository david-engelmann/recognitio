[Back to the documentation index](README.md)

# The Cursor Marketplace submission pack

## At a glance

**What ships**

This pack and nothing else. It holds the filing route for the
Cursor Marketplace, the requirement set read from the primary
Cursor pages, and an evidence check of every requirement
against the shipped tree, so the filing can go ahead on the
decision of the owner without further research.

**What was proven**

Every requirement the primary pages state was checked against
the shipped manifests and files on 2026-10-27. The gate at
scripts/check_submissions.py pins the facts the check rests
on, so drift in a manifest or in this pack fails the gate.

**What is unverified**

The publish form stands behind a sign in and its field list
is unverified. No primary page states a review timeline, so
this pack promises none.

## Summary

Nothing in this pack has been submitted. The pack is written
against version 1.3.0 of recognitio. Requirements were read
from the primary sources named in this pack on 2026-10-27.
The Cursor plugin already ships in this repo in the shape the
marketplace reviews, and the evidence check below finds the
requirement set met in substance. One item stands partly met,
the local test, for reasons of timing and of a login wall
rather than of the tree. Three open points stand recorded
after it, and those are conflicts or silences in the primary
sources. Filing is one signed in form by the owner, and
what that involves stands in the filing steps below.

## The route

A ready plugin is submitted for review at
cursor.com/marketplace/publish. The marketplace is curated
rather than self serve. Every plugin is manually reviewed
before it is listed, and every update is manually reviewed
before it is published, with explicit approval required. The
review covers security, data handling and quality. All
marketplace plugins must be open source, and the plugin must
be hosted in a public Git repository before submission. No
primary page states a review duration or a response window,
and Cursor staff state in the forum that no service level
exists and that timelines vary.

## What the listing needs

The manifest at .cursor-plugin/plugin.json is the listing
source. The reference names one required field, the name,
which must be lowercase kebab-case and unique. The submission
checklist adds the substance around it. The description must
clearly explain the purpose of the plugin. Every included
component must carry valid files and valid frontmatter, with
skills and agents carrying a name and a description and rules
carrying a description and an alwaysApply field. A logo is
optional but recommended, and a provided logo must be
committed to the repo and referenced by a relative path. A
README must document usage and any configuration. Every
manifest path must be relative, with no parent references and
no absolute paths. A plugin that uses variable placeholders
in an MCP file must declare each one in the manifest
variables schema. A multi plugin repo carries
.cursor-plugin/marketplace.json at its root with unique
plugin names, and the marketplace file itself must stay at
or under 10 MB. The checklist closes on local testing, done
by placing the plugin in the local plugins folder, reloading
the window, and confirming the components in Customize.

## The evidence check

**Met, the manifest.** The shipped manifest carries the name
recognitio in lowercase kebab-case, a description that states
the purpose in the canonical sentence, an author object with
a name and an email, the license value MIT, and the homepage
and repository values pointing at the public repo. The
discovery fields the manifest schema names stand filled, as
the discovery gate pins.

**Met, the logo.** The manifest logo value is a relative path
to docs/brand/recognitio-icon.svg, committed in the repo. No
primary page states a logo size, a format list, or a file
size limit, so no size claim is made for the asset.

**Met, the components.** The skills field points at the real
directory copy of the skill, whose SKILL.md carries a name
and a description in its frontmatter. The one rule file
carries a description and an alwaysApply field in its
frontmatter. The plugin ships no MCP file, so the variable
declaration item has nothing to declare.

**Met, the marketplace file.** The file at
.cursor-plugin/marketplace.json carries the required name
and owner fields and one plugin entry for recognitio with
the root as its source, and it weighs a few hundred bytes
against the 10 MB limit.

**Met, the README.** The repo root README documents what the
tool does and how it is installed and used, and the plugin
folder carries its own README for the plugin shape.

**Partly met, the local test.** The official desktop client
loaded this plugin from the local plugins folder with zero
failures in the run recorded in the Cursor brief, and the
Customize backing records listed its skill and its rule. Two
limits ride with that record. The rendered Customize page
stayed unobserved behind the login wall of the client, so
the confirmation rests on the backing records rather than on
the page itself. And the run predates the logo value a later
round added to the manifest, so the copy that was loaded is
not the shipped manifest in that one field. A fresh local
load of the shipped plugin stands as a small pre-filing
step, and the verdict here is partly met rather than met.

**Met, no binaries.** The plugin components are markdown,
JSON, and Python source, with no compiled binary among them,
which is the shape the security page describes.

**Not required, screenshots.** No primary page asks a plugin
listing for screenshots or a social preview. The brand
assets in this repo stand ready for other surfaces and are
not a filing blocker here.

**Met, open source.** The repo is public and MIT licensed,
which is the listing condition the primary pages state.

## The open points

The first is a conflict between two primary sources. The docs
reference tables place category and tags as marketplace
entry fields, while the manifest schema the Cursor project
ships places them in the manifest and names no discovery
field on the entry. The shipped tree follows the schema, the
stricter and machine readable source, and the discovery gate
pins that shape. If a reviewer asks for the fields on the
entry, adding them is a small change at filing time. This
pack adopts neither reading silently and records the conflict
as it stands.

The second is the single entry marketplace file. The Cursor
plugin template advises a single plugin repo to drop the
marketplace file and keep the plugin at the root, while the
reference describes the file as the multi plugin mechanism
without forbidding a single entry. The shipped tree keeps the
file, because its own gates pin the manifest pair and the
file does the listing no documented harm. Whether it helps
or is ignored in a public submission is unverified.

The third is a stale route in the plugin template the
Cursor project ships. Its README tells an author to have the
repo link ready for submission to the Cursor team by Slack
or an email address, which conflicts with the publish page
route both current docs pages state. This pack files by the
docs route. Which route Cursor would honour today is
unverified, and the template text is recorded here so the
conflict is not lost.

## Filing steps

1. The owner signs in to Cursor with the account that will
   own the listing.
2. The owner opens cursor.com/marketplace/publish and files
   the plugin, naming this public repo as the source.
3. The owner gives the repo URL and the plugin folder at the
   repo root when the form asks for them.
4. The owner submits and keeps the confirmation the form
   returns.
5. When Cursor replies, the owner answers any review point or
   files the small entry field change the open point above
   describes, if a reviewer asks for it.
6. On approval the listing stands at the reviewed commit,
   and each later update goes through the same review before
   it publishes.

## What remains David's act

The filing itself. The form is tied to the signed in account,
and its owner field shows that account email, greyed out and
labelled as submitting as an individual, with no way to file
as a company instead. The stated workaround for naming is the
author name in the manifest, which the shipped manifest
already carries. No agent can file the form, own the owner
identity, or receive the review correspondence in place of
the account holder. The owner also carries the standing
obligation the security page states, to respond to reported
security or stability issues, since an author who does not
risks losing good standing and being delisted.

## What is unverified

The field list on the publish form is unverified, because the
page returns no readable form text without a sign in. Name
uniqueness in the marketplace is unverified, because no
primary source lets an outsider prove a negative. No review
timeline is stated anywhere primary, so none is promised.
Whether Cursor Directory is a recommended first step is a
forum account of one case and is not treated as a requirement
here.

## Sources

- The plugins overview at https://cursor.com/docs/plugins
- The plugins reference at https://cursor.com/docs/reference/plugins
- The marketplace security page at https://cursor.com/help/security-and-privacy/marketplace-security
- The plugin template at https://github.com/cursor/plugin-template
- The staff forum thread on submitting as a company at https://forum.cursor.com/t/cursor-plugin-submit-as-company-not-individual/156274

## Navigation

- [Documentation index](README.md)
- [Decisions](decisions.md)
- [Principles](principles.md)
