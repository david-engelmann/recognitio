#!/usr/bin/env python3
"""Fixture blocking check for the Kimi hook live test.

Takes the hook event name and a mode. Prints the event it ran
and exits nonzero when the mode is fail, which the blocking
posture reads as a stopped turn.
"""

import sys

event = sys.argv[1]
mode = sys.argv[2]
print("hook event " + event)
sys.exit(1 if mode == "fail" else 0)
