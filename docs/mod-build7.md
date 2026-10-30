[Back to the documentation index](README.md)

# The Build 7 mod, in process hooks for the review fan out

## At a glance

**What ships**

The hooks module under `hooks/` with its host side tests, registering one agent.spawn hook that gates a reviewer spawn on the packet manifest verified flag, and the recognitio-mod marketplace entry under `plugins/recognitio-mod/` carrying byte identical copies of the module.

**What was proven**

The module validates clean on Claude Code 2.1.314 with its agent.spawn hook named in the gating hooks report with its catch flag set, and the module ran live on that build across headless sessions, a streamed session, the marketplace install route and the root plugin route. The five packet states stand proven on the headless route, where a spawn over a verified packet passed, a spawn over an unverified packet was denied in the gate's own words, spawns over a missing or corrupt manifest were denied through the catch handler, and a spawn with no packet configured proceeded untouched. The unverified packet was also denied on the streamed, marketplace and root plugin routes.

**What is unverified**

Agent team teammate spawns, the Desktop and VS Code surfaces, and an induced catch handler timeout stand unverified. The catch handler limit itself stands as the recorded limit section states it, on the primary events guide's word and the reference's one second limit for catch handlers.

## Summary

Build 7 adds an in process hook on the home platform that reads
the packet manifest when a reviewer spawn is about to start and
lets the spawn through only when the manifest reads verified.
The mod ships in this repo as the hooks module and its host side
tests under hooks, beside the portable core and outside the
canonical skill text. The contract lives in the sections below,
and the gate at scripts/check_mod.py pins the module list, the
spawn hook and its fail closed deny handler.

This document is the brief for the Build 7 Claude Code mod.
The mod lives under `hooks/` beside the portable core, not
in the canonical skill text. It exploits the Mods surface,
the strongest enforcement point on the home platform, with
the `agent.spawn` handler gating the reviewer fan out and
the `.catch` handler returning a deny shape as the fail
closed mechanism. Decision 4 binds this build like every
other build.

The marketplace listing at `.claude-plugin/marketplace.json`
offers the mod as its own marketplace entry, named
recognitio-mod and sourced from `plugins/recognitio-mod/`.
That folder carries its own manifest and byte identical
copies of the hooks module, its host side tests and the
root LICENSE, so a setup can install the spawn gate
without the skill bundle. The gate pins the copies to
the originals, so the two can never drift apart. The main recognitio
plugin already includes the mod, because the hooks folder
at the repo root loads with that plugin, and the install
prose tells the reader to install one shape or the other
and never both.

## What the mod does

The hooks module at `hooks/register.js` registers one hook
on the `agent.spawn` event. When a subagent or an agent team
teammate is about to start, the hook reads the review packet
manifest named by the `RECOGNITIO_PACKET_DIR` environment
variable and applies the shipped deterministic rule. The
manifest's `verified` flag is the whole check. A packet
whose manifest reads verified lets the spawn through. A
packet whose manifest is missing, unreadable, unparsable,
or not verified denies the spawn with a reason. When no
packet directory is configured, the mod is inert and the
spawn passes through, because the mod enforces the review
workflow and is not a global spawn gate.

The hook never calls a model. No model judgment replaces
the manifest check. The hook's only mods API calls are
`$.fs.read` and `$.env.get`.

The mod needs Claude Code v2.1.287 or later, the first
build with mods, and stands live tested on 2.1.314.

## The fail closed mechanism

The `agent.spawn` registration carries a `.catch` handler.
A hook refuses an action by returning the deny shape, and
the events guide prescribes the catch handler as the way a
hook that blocks calls keeps its refusal standing when the
hook itself fails. When the gate hook throws or times out before it
answers, the host calls the catch handler with the same
event, and the handler returns the deny shape for
`agent.spawn`, which is `{ deny: reason }`. A crashed hook
denies the spawn rather than letting it through. That is
the fail closed mechanism, and the gate pins it. A mod
hook shipped without a `.catch` handler fails the repo
gate.

## The recorded limit

If the catch handler itself throws or times out, the host
skips the hook as if it had no handler and the spawn
proceeds. A hook crash is denied only while the catch
handler itself runs clean. This second layer fail open is
a stated limit of the build, not a surprise. The brief
states it here and the gate pins the sentence, so a later
edit cannot quietly drop the limit.

## The gating boundary

The hook sees only in session agent spawns. Reviewers the
Build 6 runbook starts as `claude -p` subprocesses are not
in session spawns, and the mod does not see them. That
path stays gated by the run record validator at
`scripts/check_fanout.py`, not by this mod. The mod and
the validator cover different spawn shapes, and the brief
states which is which so no reader mistakes the
enforcement for wider than it is.

## The disabled mods degradation

When mods are disabled or unavailable, the mod never
loads and nothing about the scripts changes. The packet
is still gated by `scripts/check_packet.py` before any
reviewer spawns, and the run record is still gated by
`scripts/check_fanout.py` after the second pass. The mod
wraps the gate and degrades gracefully to it, which is
what decision 4 requires.

## The deployment gate

The build's gate check on a host with the CLI is
`claude plugin validate --json` on the plugin
directory. Its `gatingHooks` report names every mod
hook that can refuse an action with a `hasCatch`
flag, and the build requires the flag set on the
`agent.spawn` hook. On Claude Code 2.1.314 the report
names the hook exactly so, in the contents entry for
`hooks/hooks.json`. Validation refuses a module whose
environment read names its variable through anything
but a string literal, which is how the first shipped
module failed, as the live run correction below
records. The options object file read passes
validation, and only the live run and the repo gate
below catch that shape. The host side test
story is `claude plugin test`, which runs the
`*.test.ts` files under `hooks/` with no session,
sign in, or network, firing the event through the
loaded module against stubs in the documented shapes.
Where the CLI is absent, the repo
gate pins the same contract deterministically. The
`hooks/hooks.json` module list, the `.catch` handler,
the deny shape, the literal environment name, the
path only file read, and the limit sentence above are
all pinned by `scripts/check_mod.py`.

## What the brief strikes

The `onFailure` language is struck from this brief as a
category error. That setting belongs to command and HTTP
settings hooks, not to mods. The `--mod` flag is struck.
The one session flags are `--plugin-dir` and
`--plugin-url`. The `agent.spawn` claim narrows to model
choice and deny, which is what the primary Mods
reference documents. Prompt rewriting by the hook is now
primary documented. The v2.1.300 release notes and the
October 14 2026 docs changelog both document the
prompt.change mod hook. The mods reference return table
lags behind, showing model choice and deny only, stamped
as of v2.1.290.

## The scheduled execution reconciliation

The mod leaves `disable-model-invocation` at its default
false and withholds the skill through no deny rule, so
scheduled runs through `/loop` keep working. Setting the
flag true would turn scheduled fires into plain text
sends, which is the failure mode the primary scheduled
tasks page warns about.

## The live run correction

The module as first shipped never ran. Its environment
read passed a variable where the host requires a string
literal at the call site, so validation failed on the
module and the host refused to load it in a session,
and a spawn over an unverified packet proceeded with
no gate at all. Its file read passed an options object
where the host takes the path alone, and no repo gate
could see either defect, because the host side tests
stubbed the calls in the same shapes the code assumed.
A live run on Claude Code 2.1.314 in an OpenRouter
backed session caught both. This pass corrects the two
call sites, rebuilds the host
side tests on the test kit engine with stubs in the
documented shapes, pins both call shapes in the repo
gate, and gives the mod entry the brand icon its
manifest lacked.

## Skill tightness

The mod, its tests, and this brief live outside the
canonical skill text under `hooks/` and `docs/`. The
skill description is untouched, so the description
protocol does not fire. The deliverable remains the
skill.

## Navigation

- [Documentation index](README.md)
- [Decisions](decisions.md)
- [Principles](principles.md)
