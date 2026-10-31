#!/usr/bin/env python3
"""The Build 12 PreToolUse packet gate hook.

The Antigravity host runs this script as the command handler
of the one PreToolUse entry in .antigravity/hooks.json. The
host sends the event details as JSON on stdin, with the tool
call under the toolCall field, and reads one JSON object on
stdout carrying the required decision field.

The decision restates the packet discipline of the canonical
skill. The packet manifest the review run rests on is named
by the RECOGNITIO_PACKET_MANIFEST environment variable when
it is set, and otherwise the script reads manifest.json at
the root of each workspace path the event names, in order.
A manifest that does not stand at any of those places is
missing, and the decision is deny. A manifest that stands
but cannot be read or parsed leaves the packet unprovable,
and the decision is force_ask. A manifest whose verified
flag reads true earns auto_approve, and a manifest whose
verified flag reads anything else earns deny, because a
review never begins on a packet whose verified flag is
false. The manifest reading refuses a repeated key the
way every other trusted reader in this repo does, so a
manifest that names one key twice is unparsable here and
earns force_ask rather than letting the last value win.
An event payload the script cannot parse is held
for user confirmation the same way, because no manifest
reading can be trusted from it.

The script exits 0 on every path. The decision field on
stdout carries the outcome, and no exit code is a second
channel for it.
"""

import json
import os
import sys
from pathlib import Path

ENV_VAR = "RECOGNITIO_PACKET_MANIFEST"


def strict_json_loads(text):
    """Parse JSON refusing a repeated key, like the other gates."""
    def reject(pairs):
        seen = {}
        for key, value in pairs:
            if key in seen:
                raise ValueError("repeated key %r" % key)
            seen[key] = value
        return seen
    return json.loads(text, object_pairs_hook=reject)


def manifest_candidates(payload):
    """The manifest paths to try, in order."""
    named = os.environ.get(ENV_VAR)
    if named:
        return [Path(named)]
    paths = []
    workspaces = payload.get("workspacePaths")
    if isinstance(workspaces, list):
        for entry in workspaces:
            if isinstance(entry, str) and entry:
                paths.append(Path(entry) / "manifest.json")
    return paths


def decide(payload):
    """The (decision, reason) pair for one event payload."""
    if not isinstance(payload, dict):
        return (
            "force_ask",
            "the hook event payload is not a JSON object, so "
            "the packet cannot be proven whole",
        )
    candidates = manifest_candidates(payload)
    for candidate in candidates:
        if candidate.is_file():
            try:
                data = strict_json_loads(
                    candidate.read_text(encoding="utf-8")
                )
            except (OSError, UnicodeDecodeError, ValueError):
                return (
                    "force_ask",
                    "the packet manifest is unreadable or "
                    "unparsable, so the tool call is held for "
                    "user confirmation",
                )
            if isinstance(data, dict) and data.get("verified") is True:
                return (
                    "auto_approve",
                    "the packet manifest reads verified, so "
                    "the tool call proceeds without asking",
                )
            return (
                "deny",
                "the packet manifest is not verified, so "
                "the tool call is refused",
            )
    return (
        "deny",
        "the packet manifest is missing, so the tool call "
        "is refused",
    )


def main():
    try:
        payload = json.load(sys.stdin)
    except ValueError:
        payload = None
    decision, reason = decide(payload)
    print(json.dumps({"decision": decision, "reason": reason}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
