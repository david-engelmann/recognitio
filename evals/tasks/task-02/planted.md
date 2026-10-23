# Planted defects for task-02

Title. A parser stops raising and gains an off by one

Grader only. Do not read this file during either review pass.

## D1 (packet)

test_parse.py still expects ValueError for a bad port, and the unchanged server.py passes the result on unchecked, so bad input now flows through as None instead of failing. A pass finds this only when it names the test expectation or the unchecked caller in server.py.

## D2 (diff)

Valid ports come back one higher than the number given, because the new return line adds one. The line sits in the diff itself.
