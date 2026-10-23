# The pericope for range HEAD~1..HEAD

A recognitio review packet. It holds the change and the context appointed to be read with it, and nothing else.

Mode: range
Base: 3f80507942e960215635593b9a92438e7b065818
Head: 21ec2aa7a91343c9bdf487a872593b5067c07c06
Merge base: 3f80507942e960215635593b9a92438e7b065818
Verified: yes

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
21ec2aa commit
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
1: from util import add
5:     assert add(2, 3) == 5
```

## T3 History

### Blame summary for changed ranges

#### page.py

```
Test User 21ec2aa7 lines 2
```

#### util.py

```
Test User 21ec2aa7 lines 4
```

### Recent evolution of changed functions

#### heading_total in page.py

```
commit 21ec2aa commit

diff --git a/page.py b/page.py
--- a/page.py
+++ b/page.py
@@ -4,2 +4,2 @@
 def heading_total(qty, rate):
-    return add(qty, rate)
+    return add_tax(qty, rate)
commit 3f80507 commit

diff --git a/page.py b/page.py
--- /dev/null
+++ b/page.py
@@ -0,0 +4,2 @@
+def heading_total(qty, rate):
+    return add(qty, rate)
```

#### add in util.py

```
commit 21ec2aa commit

diff --git a/util.py b/util.py
--- a/util.py
+++ b/util.py
@@ -1,2 +1,4 @@
 def add(a, b):
     return a + b
+
+
commit 3f80507 commit

diff --git a/util.py b/util.py
--- /dev/null
+++ b/util.py
@@ -0,0 +1,2 @@
+def add(a, b):
+    return a + b
```

#### add_tax in util.py

```
commit 21ec2aa commit

diff --git a/util.py b/util.py
--- a/util.py
+++ b/util.py
@@ -3,0 +5,2 @@
+def add_tax(amount, tax):
+    return add(amount, tax)
```

### Prior pull requests touching these files

Scope of the lookup: the 3 most changed files, checked against the 30 most recent pull requests, with at most 5 matches shown. A pull request outside that window is not reported here.

Prior pull requests are unavailable in this environment. The GitHub CLI is missing or this clone is not a GitHub checkout, so no pull request history was gathered.

## Budget and completeness

Budget in tokens: none set
Packet estimate in tokens: 975
T0 included at about 42 tokens across 2 files
T1 included at about 153 tokens across 2 files
T2 included at about 229 tokens across 2 files
T3 included at about 365 tokens across 2 files
No tier was dropped.

Completeness check passed. A separate recount of files, statuses, old paths, hunks and lines matches the manifest.
