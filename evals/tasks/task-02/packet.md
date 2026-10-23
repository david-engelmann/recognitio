# The pericope for range 9a422a7c8fdb57efb50b1fa93ba604bb52712e99..d6af5760ead34f0b2cf23e7dd2d643eaf28bfa4d

A recognitio review packet. It holds the change and the context appointed to be read with it, and nothing else.

Mode: range
Base: 9a422a7c8fdb57efb50b1fa93ba604bb52712e99
Head: d6af5760ead34f0b2cf23e7dd2d643eaf28bfa4d
Merge base: 9a422a7c8fdb57efb50b1fa93ba604bb52712e99
Verified: yes

## T0 Triage

Files changed: 1

### Files

- parse.py (modified)

### Numstat

```
3	1	parse.py
```

### Commits

```
d6af576 change under review
```

## T1 The change

Each file shows its diff with whole enclosing function context.

### parse.py

Status: modified

```diff
diff --git a/parse.py b/parse.py
index 1a21324..165412f 100644
--- a/parse.py
+++ b/parse.py
@@ -1,2 +1,4 @@
 def parse_port(text):
-    return int(text)
+    if not text.isdigit():
+        return None
+    return int(text) + 1
```

## T2 Companions

Call sites, imports, definitions and test files found by deterministic search at the head revision.

### Call sites for parse_port in parse.py

```
server.py:1: from parse import parse_port
server.py:2: 

server.py:4: def start(text):
server.py:5:     return parse_port(text)

test_parse.py:2: 
test_parse.py:3: from parse import parse_port
test_parse.py:4: 

test_parse.py:7:     with pytest.raises(ValueError):
test_parse.py:8:         parse_port("abc")

```

### Imports of the changed files

No import lines were found in the changed source files.

### Definitions of changed names elsewhere

No definitions of the changed names were found outside the changed files.

### Test files that mention the changed code

#### test_parse.py

```
3: from parse import parse_port
8:         parse_port("abc")
```

## T3 History

### Blame summary for changed ranges

#### parse.py

```
Eval Fixture d6af5760 lines 3
```

### Recent evolution of changed functions

#### parse_port in parse.py

```
commit d6af576 change under review

diff --git a/parse.py b/parse.py
--- a/parse.py
+++ b/parse.py
@@ -1,2 +1,4 @@
 def parse_port(text):
-    return int(text)
+    if not text.isdigit():
+        return None
+    return int(text) + 1
commit 9a422a7 base

diff --git a/parse.py b/parse.py
--- /dev/null
+++ b/parse.py
@@ -0,0 +1,2 @@
+def parse_port(text):
+    return int(text)
```

### Prior pull requests touching these files

Scope of the lookup: the 3 most changed files, checked against the 30 most recent pull requests, with at most 5 matches shown. A pull request outside that window is not reported here.

Prior pull requests are unavailable in this environment. The GitHub CLI is missing or this clone is not a GitHub checkout, so no pull request history was gathered.

## Budget and completeness

Budget in tokens: none set
Packet estimate in tokens: 775
T0 included at about 37 tokens across 1 files
T1 included at about 89 tokens across 1 files
T2 included at about 206 tokens across 1 files
T3 included at about 240 tokens across 1 files
No tier was dropped.

Completeness check passed. A separate recount of files, statuses, old paths, hunks and lines matches the manifest.
