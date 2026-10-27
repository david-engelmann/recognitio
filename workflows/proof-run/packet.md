# The pericope for range bc6e67513b383f4c25b38bda4fbfc68035fa40f0..dbe5978fb89b0c135947b3d9487d126ec13890fd

A recognitio review packet. The pericope named in the title is this packet, holding the change and the context a reviewer needs to read it, and nothing else.

Mode: range

Base: bc6e67513b383f4c25b38bda4fbfc68035fa40f0

Head: dbe5978fb89b0c135947b3d9487d126ec13890fd

Merge base: bc6e67513b383f4c25b38bda4fbfc68035fa40f0

Verified: yes. The recount at the close of this packet carries the proof.

Contents

This packet holds 4 files, 4 hunks, 13 added lines and 3 deleted lines

All four tiers stand in full

The tiers, in order

- T0 Triage
- T1 The change
- T2 Companions
- T3 History

The close

- Verification recount

## T0 Triage

Files changed: 4

### Files

- src/a.py (modified)
- src/b.py (modified)
- src/c.py (modified)
- src/d.py (modified)

### Numstat

```
1	0	src/a.py
1	1	src/b.py
10	1	src/c.py
1	1	src/d.py
```

### Commits

```
dbe5978 head change
```

## T1 The change

Each file shows its diff with whole enclosing function context.

### src/a.py

Status: modified

```diff
diff --git a/src/a.py b/src/a.py
index 9f2c28e..2d6a930 100644
--- a/src/a.py
+++ b/src/a.py
@@ -1,3 +1,4 @@
+import os
 import sys
 
 def main():
```

### src/b.py

Status: modified

```diff
diff --git a/src/b.py b/src/b.py
index 4c8b581..2f80af0 100644
--- a/src/b.py
+++ b/src/b.py
@@ -1,2 +1,2 @@
 def helper():
-    return 1
+    return 10
```

### src/c.py

Status: modified

```diff
diff --git a/src/c.py b/src/c.py
index 55b945d..4c0a825 100644
--- a/src/c.py
+++ b/src/c.py
@@ -1,2 +1,11 @@
 def fetch(url):
-    return open(url).read()
+    try:
+        return open(url).read()
+    except ValueError:
+        API_KEY = 'fake-live-key-123'
+        raise
+def load(url):
+    try:
+        return open(url).read()
+    except Exception:
+        pass
```

### src/d.py

Status: modified

```diff
diff --git a/src/d.py b/src/d.py
index 7a3ad00..9ee1f09 100644
--- a/src/d.py
+++ b/src/d.py
@@ -1,2 +1,2 @@
 def util():
-    return 2
+    return 20
```

## T2 Companions

Call sites, imports, definitions and test files found by deterministic search at the head revision.

### Call sites for main in src/a.py

No call sites found outside the changed file.

### Call sites for helper in src/b.py

No call sites found outside the changed file.

### Call sites for fetch in src/c.py

No call sites found outside the changed file.

### Call sites for load in src/c.py

No call sites found outside the changed file.

### Call sites for util in src/d.py

No call sites found outside the changed file.

### Imports of the changed files

#### src/a.py

```
1: import os
2: import sys
```

### Definitions of changed names elsewhere

No definitions of the changed names were found outside the changed files.

### Test files that mention the changed code

No test files mention the changed modules or functions.

## T3 History

### Blame summary for changed ranges

#### src/c.py

```
Proof Fixture dbe5978f lines 10
```

#### src/b.py

```
Proof Fixture dbe5978f lines 1
```

#### src/d.py

```
Proof Fixture dbe5978f lines 1
```

### Recent evolution of changed functions

#### fetch in src/c.py

```
commit dbe5978 head change

diff --git a/src/c.py b/src/c.py
--- a/src/c.py
+++ b/src/c.py
@@ -1,2 +1,6 @@
 def fetch(url):
-    return open(url).read()
+    try:
+        return open(url).read()
+    except ValueError:
+        API_KEY = 'fake-live-key-123'
+        raise
commit bc6e675 base

diff --git a/src/c.py b/src/c.py
--- /dev/null
+++ b/src/c.py
@@ -0,0 +1,2 @@
+def fetch(url):
+    return open(url).read()
```

#### load in src/c.py

```
commit dbe5978 head change

diff --git a/src/c.py b/src/c.py
--- a/src/c.py
+++ b/src/c.py
@@ -2,1 +7,5 @@
-    return open(url).read()
+def load(url):
+    try:
+        return open(url).read()
+    except Exception:
+        pass
commit bc6e675 base

diff --git a/src/c.py b/src/c.py
--- /dev/null
+++ b/src/c.py
@@ -0,0 +2,1 @@
+    return open(url).read()
```

#### helper in src/b.py

```
commit dbe5978 head change

diff --git a/src/b.py b/src/b.py
--- a/src/b.py
+++ b/src/b.py
@@ -1,2 +1,2 @@
 def helper():
-    return 1
+    return 10
commit bc6e675 base

diff --git a/src/b.py b/src/b.py
--- /dev/null
+++ b/src/b.py
@@ -0,0 +1,2 @@
+def helper():
+    return 1
```

### Prior pull requests touching these files

Scope of the lookup: the 3 most changed files, checked against the 30 most recent pull requests, with at most 5 matches shown. A pull request outside that window is not reported here.

Prior pull requests are unavailable in this environment. The GitHub CLI is missing or this clone is not a GitHub checkout, so no pull request history was gathered.

## Verification recount

### Budget

Budget in tokens: none set

Packet estimate in tokens: 1355

T0 included at about 62 tokens across 4 files

T1 included at about 271 tokens across 4 files

T2 included at about 212 tokens across 4 files

T3 included at about 453 tokens across 3 files

No tier was dropped.

### Recount

Recount passed

A separate recount counted the change a second time

The recount covered 4 files with their statuses and old paths, 4 hunks, and 13 added lines and 3 deleted lines

The recount matches the manifest on every count

Every tier is included

Verified means this packet holds the whole change it names

Verified does not mean the change is correct or safe
