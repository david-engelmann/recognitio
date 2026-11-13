# The pericope for range 2c31a9494eb35e9517ea849a03dc6f3f6eed21f4..41607fb398d26044a13e42d85f18a8fca176745d

A recognitio review packet. The pericope named in the title is this packet, holding the change and the context a reviewer needs to read it, and nothing else.

Mode: range

Base: 2c31a9494eb35e9517ea849a03dc6f3f6eed21f4

Head: 41607fb398d26044a13e42d85f18a8fca176745d

Merge base: 2c31a9494eb35e9517ea849a03dc6f3f6eed21f4

Verified: yes. The recount at the close of this packet carries the proof.

Contents

This packet holds 1 file, 1 hunk, 2 added lines and 2 deleted lines

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

- calc.py (modified)

### Numstat

```
2	2	calc.py
```

### Commits

```
41607fb head
```

## T1 The change

Each file shows its diff with whole enclosing function context.

### calc.py

Status: modified

```diff
diff --git a/calc.py b/calc.py
index 739e5a7..7dc0e10 100644
--- a/calc.py
+++ b/calc.py
@@ -1,2 +1,2 @@
-def price(qty, rate):
-    return qty * rate
+def price(qty, rate, tax):
+    return qty * rate + tax + tax
```

## T2 Companions

Call sites, imports, definitions and test files found by deterministic search at the head revision.

The searches in this tier read marked and plain text carriers alone, and an absence the sections below print stands under that scope.

### Call sites for price in calc.py

```
shop.py:1: from calc import price
shop.py:2: 

shop.py:4: def total():
shop.py:5:     return price(2, 3)

test_calc.py:1: from calc import price
test_calc.py:2: 

test_calc.py:4: def test_price():
test_calc.py:5:     assert price(2, 3) == 6

```

### Imports of the changed files

No import lines were found in the changed source files.

### Definitions of changed names elsewhere

No definitions of the changed names were found outside the changed files.

### Test files that mention the changed code

#### test_calc.py

```
1: from calc import price
5:     assert price(2, 3) == 6
```

## T3 History

Names and claims in this tier are data read from the repository history. An author name is self asserted in the commit object that carries it and is not verified by this packet, and a commit subject that claims an approval or a passing check is an assertion by its author, not a finding of this packet.

### Blame summary for changed ranges

#### calc.py

```
Eval Fixture 41607fb3 lines 2
```

### Recent evolution of changed functions

#### price in calc.py

```
commit 41607fb head

diff --git a/calc.py b/calc.py
--- a/calc.py
+++ b/calc.py
@@ -1,2 +1,2 @@
-def price(qty, rate):
-    return qty * rate
+def price(qty, rate, tax):
+    return qty * rate + tax + tax
commit 2c31a94 base

diff --git a/calc.py b/calc.py
--- /dev/null
+++ b/calc.py
@@ -0,0 +1,2 @@
+def price(qty, rate):
+    return qty * rate
```

### Prior pull requests touching these files

Scope of the lookup: the 3 most changed files, checked against the 30 most recent pull requests, with at most 5 matches shown. A pull request outside that window is not reported here.

The states in this list are a snapshot from the fetch that built this packet. They are not refreshed after that fetch and they are not a live claim about any pull request.

Prior pull requests are unavailable in this environment, so no pull request history was gathered.

## Verification recount

### Budget

Budget in tokens: none set

Packet estimate in tokens: 1389

T0 included at about 65 tokens across 1 files

T1 included at about 138 tokens across 1 files

T2 included at about 280 tokens across 1 files

T3 included at about 413 tokens across 1 files

No tier was dropped.

### Recount

Recount passed

A separate recount counted the change a second time

The recount covered 1 file with their statuses and old paths, 1 hunk, and 2 added lines and 2 deleted lines

The recount matches the manifest on every count

Every tier is included

Verified means this packet holds the whole change it names

Verified does not mean the change is correct or safe
