# The Build 7 mod, in process hooks for the review fan out

This document is the brief for the Build 7 Claude Code mod.
The mod lives under `hooks/` beside the portable core, not
in the canonical skill text. It exploits the Mods surface,
the strongest enforcement point on the home platform, with
the `agent.spawn` handler gating the reviewer fan out and
the `.catch` handler returning a deny shape as the fail
closed mechanism. Decision 4 binds this build like every
other build.

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

## The fail closed mechanism

The `agent.spawn` registration carries a `.catch` handler,
as the Mods reference requires for a hook that refuses an
action. When the gate hook throws or times out before it
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
`claude plugin validate --json`. Its `gatingHooks`
report names every mod hook that can refuse an action
with a `hasCatch` flag, and the build requires the
flag set on the `agent.spawn` hook. The host side test
story is `claude plugin test`, which runs the
`*.test.ts` files under `hooks/` with no session,
sign in, or network. Where the CLI is absent, the repo
gate pins the same contract deterministically. The
`hooks/hooks.json` module list, the `.catch` handler,
the deny shape, and the limit sentence above are all
pinned by `scripts/check_mod.py`.

## What the brief strikes

The `onFailure` language is struck from this brief as a
category error. That setting belongs to command and HTTP
settings hooks, not to mods. The `--mod` flag is struck.
The one session flags are `--plugin-dir` and
`--plugin-url`. The `agent.spawn` claim narrows to model
choice and deny, which is what the primary Mods
reference documents. Prompt rewriting by the hook stays
unverified on the primary evidence.

## The scheduled execution reconciliation

The mod leaves `disable-model-invocation` at its default
false and withholds the skill through no deny rule, so
scheduled runs through `/loop` keep working. Setting the
flag true would turn scheduled fires into plain text
sends, which is the failure mode the primary scheduled
tasks page warns about.

## Skill tightness

The mod, its tests, and this brief live outside the
canonical skill text under `hooks/` and `docs/`. The
skill description is untouched, so the description
protocol does not fire. The deliverable remains the
skill.
