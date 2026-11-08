# The pericope for range bcc5630c50c8d2288132d2c3d9874ff29f0823f6..90c57f7d9b9ebc4a1a830b0fc4c01025a1b1d6fd

A recognitio review packet. The pericope named in the title is this packet, holding the change and the context a reviewer needs to read it, and nothing else.

Mode: range

Base: bcc5630c50c8d2288132d2c3d9874ff29f0823f6

Head: 90c57f7d9b9ebc4a1a830b0fc4c01025a1b1d6fd

Merge base: bcc5630c50c8d2288132d2c3d9874ff29f0823f6

Verified: yes. The recount at the close of this packet carries the proof.

Contents

This packet holds 1 file, 1 hunk, 1 added line and 1 deleted line

All four tiers stand in full

The tiers, in order

- T0 Triage
- T1 The change
- T2 Companions
- T3 History

The close

- Verification recount

## T0 Triage

Files changed: 1

### Files

- book.py (renamed from ledger.py)

### Numstat

```
1	1	book.py
```

### Commits

```
90c57f7 head
```

## T1 The change

Each file shows its diff with whole enclosing function context.

### book.py

Status: renamed
Renamed from: ledger.py

```diff
diff --git a/ledger.py b/book.py
similarity index 68%
rename from ledger.py
rename to book.py
index 7d539f5..e0b6259 100644
--- a/ledger.py
+++ b/book.py
@@ -3,4 +3,4 @@
 
 def total(items):
     subtotal = sum(items)
-    return subtotal
+    return subtotal + subtotal
```

## T2 Companions

Call sites, imports, definitions and test files found by deterministic search at the head revision.

### Call sites for total in book.py

```
report.py:1: from ledger import total
report.py:2: 

report.py:4: def grand(items):
report.py:5:     return total(items)

test_ledger.py:1: from ledger import total
test_ledger.py:2: 

test_ledger.py:4: def test_total():
test_ledger.py:5:     assert total([1, 2]) == 3

```

### Imports of the changed files

No import lines were found in the changed source files.

### Definitions of changed names elsewhere

No definitions of the changed names were found outside the changed files.

### Test files that mention the changed code

#### test_ledger.py

```
1: from ledger import total
5:     assert total([1, 2]) == 3
```

## T3 History

Names and claims in this tier are data read from the repository history. An author name is self asserted in the commit object that carries it and is not verified by this packet, and a commit subject that claims an approval or a passing check is an assertion by its author, not a finding of this packet.

### Blame summary for changed ranges

#### book.py

```
Eval Fixture 90c57f7d lines 1
```

### Recent evolution of changed functions

#### total in book.py

```
commit 90c57f7 head

diff --git a/ledger.py b/book.py
--- a/ledger.py
+++ b/book.py
@@ -4,3 +4,3 @@
 def total(items):
     subtotal = sum(items)
-    return subtotal
+    return subtotal + subtotal
commit bcc5630 base

diff --git a/ledger.py b/ledger.py
--- /dev/null
+++ b/ledger.py
@@ -0,0 +4,3 @@
+def total(items):
+    subtotal = sum(items)
+    return subtotal
```

### Prior pull requests touching these files

Scope of the lookup: the 3 most changed files, checked against the 30 most recent pull requests, with at most 5 matches shown. A pull request outside that window is not reported here.

The states in this list are a snapshot from the fetch that built this packet. They are not refreshed after that fetch and they are not a live claim about any pull request.

Prior pull requests are unavailable in this environment. The GitHub CLI is missing or this clone is not a GitHub checkout, so no pull request history was gathered.

## Verification recount

### Budget

Budget in tokens: none set

Packet estimate in tokens: 1379

T0 included at about 71 tokens across 1 files

T1 included at about 153 tokens across 1 files

T2 included at about 257 tokens across 1 files

T3 included at about 424 tokens across 1 files

No tier was dropped.

### Recount

Recount passed

A separate recount counted the change a second time

The recount covered 1 file with their statuses and old paths, 1 hunk, and 1 added line and 1 deleted line

The recount matches the manifest on every count

Every tier is included

Verified means this packet holds the whole change it names

Verified does not mean the change is correct or safe
