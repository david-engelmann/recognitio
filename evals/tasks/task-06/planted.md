# Planted defects for task-06

Title. A module is renamed and its one caller keeps the old name

Grader only. Do not read this file during either review pass.

This task is a replay. It rebuilds at fixture scale the rename
shape that pull request 9 of this repo fixed, where a paired
rename dropped the old module name from the companion search
and the packet could print a false absence over the files that
still used that name. The finding behind the replay is R4-01 in
the round 4 audit record. The fixture change is new and the
grading below is drawn from that fix, and the task stands as a
replay rather than as a task designed in the dark.

## D1 (packet)

report.py still imports the total function from ledger at its
first line after the change renames ledger.py to book.py, so
that import names a module that no longer exists and the file
breaks at import time. A pass finds this only when it names
report.py and its import of the old module name. The test file
test_ledger.py carries the same stale import and stands as
corroborating evidence in the packet, and naming it beside
report.py strengthens the finding without replacing it.

## D2 (diff)

The subtotal is added to itself in the new return line of
book.py, so every total comes back doubled. The line sits in
the diff itself.
