#!/usr/bin/env python3
"""Fixture observation check for the Kimi hook live test.

The Kimi host runs a hook by passing the event details as
JSON on stdin, with no arguments at all. This fixture reads
that JSON, prints the event it ran, and exits 0. The four
events it serves are observation only on the host, so the
fixture blocks nothing and its exit code carries no decision
for the host to read.
"""

import json
import sys


def main():
    try:
        payload = json.load(sys.stdin)
    except ValueError:
        return 0
    if not isinstance(payload, dict):
        return 0
    event = payload.get("hook_event_name")
    if isinstance(event, str) and event:
        print("hook event " + event)
    return 0


if __name__ == "__main__":
    sys.exit(main())
