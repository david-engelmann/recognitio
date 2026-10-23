# Planted defects for task-04

Title. A render helper starts importing its own caller

Grader only. Do not read this file during either review pass.

## D1 (packet)

report.py now imports show from data.py while data.py already imports render from report.py, so importing either module can fail or bind a half built module. A pass finds this only when it names data.py as the other half of the cycle.

## D2 (diff)

The rendered string gains a trailing space and changes case in the new return line of report.py. The line sits in the diff itself.
