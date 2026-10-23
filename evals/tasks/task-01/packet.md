# The pericope for range 1741a15b4f3ccc89f0d941cc891c6de2b1ef8786..af640b42bd17ae252ebd7c281314c4f233395f67

A recognitio review packet. It holds the change and the context appointed to be read with it, and nothing else.

Mode: range
Base: 1741a15b4f3ccc89f0d941cc891c6de2b1ef8786
Head: af640b42bd17ae252ebd7c281314c4f233395f67
Merge base: 1741a15b4f3ccc89f0d941cc891c6de2b1ef8786
Verified: yes

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
af640b4 change under review
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
1: from calc import price
5:     assert price(2, 3) == 6
```

## T3 History

### Blame summary for changed ranges

#### calc.py

```
Eval Fixture af640b42 lines 2
```

### Recent evolution of changed functions

#### price in calc.py

```
commit af640b4 change under review

diff --git a/calc.py b/calc.py
--- a/calc.py
+++ b/calc.py
@@ -1,2 +1,2 @@
-def price(qty, rate):
-    return qty * rate
+def price(qty, rate, tax):
+    return qty * rate + tax + tax
commit 1741a15 base

diff --git a/calc.py b/calc.py
--- /dev/null
+++ b/calc.py
@@ -0,0 +1,2 @@
+def price(qty, rate):
+    return qty * rate
```

### Prior pull requests touching these files

Scope of the lookup: the 3 most changed files, checked against the 30 most recent pull requests, with at most 5 matches shown. A pull request outside that window is not reported here.

Prior pull requests are unavailable in this environment. The GitHub CLI is missing or this clone is not a GitHub checkout, so no pull request history was gathered.

## Budget and completeness

Budget in tokens: none set
Packet estimate in tokens: 752
T0 included at about 37 tokens across 1 files
T1 included at about 85 tokens across 1 files
T2 included at about 193 tokens across 1 files
T3 included at about 234 tokens across 1 files
No tier was dropped.

Completeness check passed. A separate recount of files, statuses, old paths, hunks and lines matches the manifest.
