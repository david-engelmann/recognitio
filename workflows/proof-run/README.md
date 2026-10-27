# The Build 6 proof run

This directory holds a complete Build 6 fan out run over a
fixture packet, and the gate validates it on every run. The
packet file and its manifest are real extractor output with
the verified flag true, built from a four file fixture
repository, and the packet file stands beside the manifest
so the validator can bind the record to the packet it
names. The run record is the ground truth below, written
by hand to show the adversarial properties the validator
pins.

## The fixture

The fixture repository holds `src/a.py`, `src/b.py`,
`src/c.py`, and `src/d.py`. The change under review
touches all four. The fixture carries one planted defect,
a hardcoded live API key at `src/c.py` line 5.

## The groups

Group g1 reads `src/a.py`, `src/b.py`, and `src/c.py`.
Group g2 reads `src/c.py` and `src/d.py`. The groups
overlap on `src/c.py`, and their union equals the manifest
file list exactly.

## Phase one

Group g1 reports two findings. Finding f1a notes the
unused `os` import at `src/a.py` line 1. Finding f2a
notes the broad except clause at `src/c.py` line 10.
Group g2 reports one finding, f2b, the same broad except
clause at the same location, raised independently. Phase
one misses the planted API key entirely.

## The merge

The merged set carries f1, raised by g1, and f2, raised
by g1 and g2, and n1, raised by the second pass and marked
with the second pass as its source. The two independent
reports of the except clause merge into one record by
their shared identity, which is the file, the line, and
the rule together. No finding is dropped and none is
counted twice.

## Phase two

The second pass confirms f1 with cited evidence, contests
f2 with cited evidence and a note saying the handler logs
and re raises, and raises n1 as a new finding for the
planted API key that phase one missed. The merged set
carries n1 as well, so a consumer reading the merged set
reads every finding the run accepted. The contest shows
the second pass is not a rubber stamp.

## Re-verifying

Run `python3 scripts/check_fanout.py` from the repo root.
It validates this record against the findings schema, the
manifest, the packet standing beside the manifest, and
the concurrency caps. Corrupt the record in any of the
ways the test suite plants and the validator fails, which
is the proof that each check is load bearing.
