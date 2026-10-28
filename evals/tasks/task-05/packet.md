# The pericope for range 0f20f931365b5c95fad8c58a66a66480f7ee0d5d..89aa079ea476007460912101d86d92d911a18bae

A recognitio review packet. The pericope named in the title is this packet, holding the change and the context a reviewer needs to read it, and nothing else.

Mode: range

Base: 0f20f931365b5c95fad8c58a66a66480f7ee0d5d

Head: 89aa079ea476007460912101d86d92d911a18bae

Merge base: 0f20f931365b5c95fad8c58a66a66480f7ee0d5d

Verified: yes. The recount at the close of this packet carries the proof.

Contents

This packet holds 2 files, 2 hunks, 6 added lines and 2 deleted lines

All four tiers stand in full

The tiers, in order

- T0 Triage
- T1 The change
- T2 Companions
- T3 History

The close

- Verification recount

## T0 Triage

Files changed: 2

### Files

- page.py (modified)
- util.py (modified)

### Numstat

```
2	2	page.py
4	0	util.py
```

### Commits

```
89aa079 head
```

## T1 The change

Each file shows its diff with whole enclosing function context.

### page.py

Status: modified

```diff
diff --git a/page.py b/page.py
index 1bdf0b3..d24a9fb 100644
--- a/page.py
+++ b/page.py
@@ -1,5 +1,5 @@
-from util import add
+from util import add_tax
 
 
 def heading_total(qty, rate):
-    return add(qty, rate)
+    return add_tax(qty, rate)
```

### util.py

Status: modified

```diff
diff --git a/util.py b/util.py
index 4693ad3..9423934 100644
--- a/util.py
+++ b/util.py
@@ -1,2 +1,6 @@
 def add(a, b):
     return a + b
+
+
+def add_tax(amount, tax):
+    return add(amount, tax)
```

## T2 Companions

Call sites, imports, definitions and test files found by deterministic search at the head revision.

### Call sites for heading_total in page.py

No call sites found outside the changed file.

### Call sites for add in util.py

```
test_util.py:1: from util import add
test_util.py:2: 

test_util.py:4: def test_add():
test_util.py:5:     assert add(2, 3) == 5

```

### Call sites for add_tax in util.py

```
page.py:1: from util import add_tax
page.py:2: 

page.py:4: def heading_total(qty, rate):
page.py:5:     return add_tax(qty, rate)

```

### Imports of the changed files

#### page.py

```
1: from util import add_tax
```

### Definitions of changed names elsewhere

No definitions of the changed names were found outside the changed files.

### Test files that mention the changed code

#### test_util.py

```
1: from util import add
5:     assert add(2, 3) == 5
```

## T3 History

### Blame summary for changed ranges

#### page.py

```
Eval Fixture 89aa079e lines 2
```

#### util.py

```
Eval Fixture 89aa079e lines 4
```

### Recent evolution of changed functions

#### heading_total in page.py

```
commit 89aa079 head

diff --git a/page.py b/page.py
--- a/page.py
+++ b/page.py
@@ -4,2 +4,2 @@
 def heading_total(qty, rate):
-    return add(qty, rate)
+    return add_tax(qty, rate)
commit 0f20f93 base

diff --git a/page.py b/page.py
--- /dev/null
+++ b/page.py
@@ -0,0 +4,2 @@
+def heading_total(qty, rate):
+    return add(qty, rate)
```

#### add in util.py

```
commit 89aa079 head

diff --git a/util.py b/util.py
--- a/util.py
+++ b/util.py
@@ -1,2 +1,4 @@
 def add(a, b):
     return a + b
+
+
commit 0f20f93 base

diff --git a/util.py b/util.py
--- /dev/null
+++ b/util.py
@@ -0,0 +1,2 @@
+def add(a, b):
+    return a + b
```

#### add_tax in util.py

```
commit 89aa079 head

diff --git a/util.py b/util.py
--- a/util.py
+++ b/util.py
@@ -3,0 +5,2 @@
+def add_tax(amount, tax):
+    return add(amount, tax)
```

### Prior pull requests touching these files

Scope of the lookup: the 3 most changed files, checked against the 30 most recent pull requests, with at most 5 matches shown. A pull request outside that window is not reported here.

The states in this list are a snapshot from the fetch that built this packet. They are not refreshed after that fetch and they are not a live claim about any pull request.

Prior pull requests are unavailable in this environment. The GitHub CLI is missing or this clone is not a GitHub checkout, so no pull request history was gathered.

## Verification recount

### Budget

Budget in tokens: none set

Packet estimate in tokens: 1749

T0 included at about 79 tokens across 2 files

T1 included at about 261 tokens across 2 files

T2 included at about 315 tokens across 2 files

T3 included at about 619 tokens across 2 files

No tier was dropped.

### Recount

Recount passed

A separate recount counted the change a second time

The recount covered 2 files with their statuses and old paths, 2 hunks, and 6 added lines and 2 deleted lines

The recount matches the manifest on every count

Every tier is included

Verified means this packet holds the whole change it names

Verified does not mean the change is correct or safe
