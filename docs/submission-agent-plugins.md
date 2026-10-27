[Back to the documentation index](README.md)

# The Agent Plugins submission pack

## At a glance

**What ships**

This pack and nothing else. Its central finding is negative
and it states that finding plainly. The Agent Plugins project
runs no directory of packages, so there is no project listing
to file for. What the pack holds instead is the conformance
check of the portable package against the published
specification and the one host listing that takes the
portable package as it stands, with its route, its criteria,
and its evidence check.

**What was proven**

The no directory finding rests on the words of the project
itself, read on 2026-10-27 and named below. The package facts
were checked against the shipped tree the same day, and the
gate at scripts/check_submissions.py pins the facts the
check rests on.

**What is unverified**

Third party sites that call themselves an Agent Plugins
directory exist on the web. They are not project properties,
no project page links to them, and their submission routes
were not verified from a primary source, so this pack treats
them as no route at all.

## Summary

Nothing in this pack has been submitted. The pack is written
against version 1.3.0 of recognitio. Requirements were read
from the primary sources named in this pack on 2026-10-27.
The Agent Plugins project runs no directory of packages. Its
implementer guide states that the format does not prescribe
installation sources, registries, or marketplaces, and its
homepage states that distribution and installation remain
under the control of each client. Distribution is therefore
a host matter by design, and the filing that exists for the
portable package is a host filing, in the Awesome Copilot
marketplace that GitHub runs for its Copilot clients. That
route, its criteria, and what remains for the owner stand
below.

## What the project offers instead

The project publishes a specification, two JSON schemas, an
author guide, an implementer guide, a page of compatible
clients, and one example package to copy. Its charter scopes
the project to the specification, reference implementations,
conformance tests, documentation, and supporting tooling.
No registry account, submission form, index file, or listing
criteria for packages stands anywhere in that set. A proposal
for a marketplace index format stands open in the project
discussions as an idea, and a second discussion records that
the first version of the specification left distribution out
on purpose. Neither is a route a package can file through
today.

The project also ships no validator. Its future
considerations file states that no test harness or
validation tool is specified, and names a linter and
conformance suites as uncommitted future ideas. Conformance
checking is therefore a self check against the published
schema and the specification text, and the specification
governs where the two disagree.

## The conformance check

**Met, the closed manifest.** The portable manifest at
agent-plugins-package/plugin.json carries only the ten top
level fields the specification permits, no more. The package
gate pins the closed set on every run.

**Met, the name.** Recognitio as a package name is lowercase
letters only, starts and ends with a letter, and stands well
inside the length and pattern rules the specification names.

**Met, the fixed locations.** The skill stands at the fixed
skills location inside the package as one child directory,
byte identical to the canonical skill, and the package gate
pins that identity on every run.

**Met, the omitted MCP file.** The package ships no MCP
file, which the specification permits, since a missing fixed
component location is not an error. The omission is the
honest shape for a package with no server to declare.

**Met, the listing shaped fields.** The manifest carries a
semantic version, a description, an author with a name, the
license value MIT, the repository as an HTTPS GitHub URL,
and a keyword set in lowercase hyphenated form. Those are
the values the host listing below asks a submission to
state, and each one already stands in the manifest it would
be read from.

## The host route that exists

Awesome Copilot is the marketplace GitHub runs for VS Code,
the Copilot CLI, the Copilot app, and the Copilot SDK, and
Agent Plugins 1.0 support stands generally available across
those clients. External plugins hosted in the repo of the
submitter are listed through a review workflow, and a direct
pull request that adds one to plugins/external.json is
refused by the contributing guide. The route is an issue
opened with the external plugin form in that repo.
Automation labels the issue, validates the metadata, and
runs its quality gates, and only a maintainer approval turns
the submission into the pull request that lists it.

The published criteria ask for a name, a description, and a
valid semantic version, an author name, the repository as an
HTTPS GitHub URL, keywords as lowercase hyphenated tags, the
source as a GitHub repo with an optional path to the folder
where the plugin structure starts, a license, and at least
one immutable locator, a ref or a full commit SHA. Its
quality gates run manifest compliance against the 1.0.0
schema, a lint pass that includes Agent Skills compliance,
an install smoke test through the Copilot CLI, and a check
that the version matches the source manifest at the pinned
locator. An approved listing is re-reviewed on a six month
cycle, and a maintainer may renew it, ask for follow up, or
remove it.

## Filing steps

1. The release tag for this version stands first, as the
   next section states, since the route needs an immutable
   locator and a branch does not serve.
2. The owner opens the external plugin issue in
   github/awesome-copilot under his own GitHub identity and
   completes the form, naming this repo, the
   agent-plugins-package folder as the plugin path, the tag
   and the full commit SHA at that tag, and the version,
   license, author, and keyword values the manifest already
   carries.
3. The owner ticks the confirmation boxes on the form, which
   attest that the repo is public, that the locator is
   immutable, that the submission follows the policies of
   that repo, and that the plugin is no duplicate listing.
4. The automated gates run against the pinned locator. A
   failure is answered by a fix in this repo and a rerun
   request on the issue, which only the issue author or a
   maintainer can post.
5. A maintainer approves or rejects. Approval opens the
   listing pull request by automation, and the listing
   stands when that request merges.

## What remains David's act

The tag and the issue. Cutting the release tag is the act of
the owner alone under the standing rule of this repo, and no
tag for this version exists yet, so the immutable locator
the route requires waits on that act. The submission issue
must be opened under his GitHub identity, because its
confirmation boxes are attestations about his own repo that
only the submitter can make. Driving the submission after
filing is his as well, since only the issue author can edit
the submission or ask for an intake rerun, and keeping the
listing through its six month re-review may ask changes of
the owner when the time comes.

## What is unverified

The exact address of the external plugin issue form is
unverified, because the contributing guide names the form
and its fields without exposing a direct link in the text
read. Host listings for the other clients the project names
were not verified from a primary source in this pass, and
that absence is recorded as unverified rather than as proof
that none exists. The Cursor Marketplace also accepts a
spec conformant plugin, and that route is prepared in the
Cursor pack in this set, which files the native shape of
this same tool.

## Sources

- The project homepage at https://agent-plugins.org/
- The specification at https://agent-plugins.org/specification
- The implementer guide at https://agent-plugins.org/client-implementers
- The author guide at https://agent-plugins.org/plugin-authors
- The compatible clients page at https://agent-plugins.org/compatible-clients
- The specification repo at https://github.com/agentplugins/agent-plugins-spec
- The Awesome Copilot contributing guide at https://github.com/github/awesome-copilot/blob/main/CONTRIBUTING.md
- The GitHub changelog on Agent Plugins 1.0 at https://github.blog/changelog/2026-08-12-agent-plugins-1-0-in-vs-code-copilot-cli-and-the-copilot-app/

## Navigation

- [Documentation index](README.md)
- [Decisions](decisions.md)
- [Principles](principles.md)
