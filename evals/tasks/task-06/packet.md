# The pericope for range 2d141304d648c099f9ba3359fcb92481335ec5dd..ee149ede0b1666c511ac14ecea8870f2c9527554

A recognitio review packet. It holds the change and the context appointed to be read with it, and nothing else.

Mode: range
Base: 2d141304d648c099f9ba3359fcb92481335ec5dd
Head: ee149ede0b1666c511ac14ecea8870f2c9527554
Merge base: 2d141304d648c099f9ba3359fcb92481335ec5dd
Verified: yes

## T0 Triage

Files changed: 1

### Files

- book.py (renamed, renamed from ledger.py)

### Numstat

```
1	1	book.py
```

### Commits

```
ee149ed rename ledger to book and change the return
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

### Blame summary for changed ranges

#### book.py

```
Test User ee149ede lines 1
```

### Recent evolution of changed functions

#### total in book.py

```
commit ee149ed rename ledger to book and change the return

diff --git a/ledger.py b/book.py
--- a/ledger.py
+++ b/book.py
@@ -4,3 +4,3 @@
 def total(items):
     subtotal = sum(items)
-    return subtotal
+    return subtotal + subtotal
commit 2d14130 base

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

Prior pull requests are unavailable in this environment. The GitHub CLI is missing or this clone is not a GitHub checkout, so no pull request history was gathered.

## Budget and completeness

Budget in tokens: none set
Packet estimate in tokens: 796
T0 included at about 48 tokens across 1 files
T1 included at about 105 tokens across 1 files
T2 included at about 195 tokens across 1 files
T3 included at about 245 tokens across 1 files
No tier was dropped.

Completeness check passed. A separate recount of files, statuses, old paths, hunks and lines matches the manifest.
