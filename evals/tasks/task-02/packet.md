# The pericope for range e637a54d903236c06074e403a16376d8d43d1600..770c08cd14543db9ee83ee2f14df6d3d3cd02151

A recognitio review packet. It holds the change and the context appointed to be read with it, and nothing else.

Mode: range
Base: e637a54d903236c06074e403a16376d8d43d1600
Head: 770c08cd14543db9ee83ee2f14df6d3d3cd02151
Merge base: e637a54d903236c06074e403a16376d8d43d1600
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
770c08c change under review
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
3: from parse import parse_port
8:         parse_port("abc")
```

## T3 History

### Blame summary for changed ranges

#### parse.py

```
Eval Fixture 770c08cd lines 3
```

### Recent evolution of changed functions

#### parse_port in parse.py

```
commit 770c08c change under review

diff --git a/parse.py b/parse.py
--- a/parse.py
+++ b/parse.py
@@ -1,2 +1,4 @@
 def parse_port(text):
-    return int(text)
+    if not text.isdigit():
+        return None
+    return int(text) + 1
commit e637a54 base

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
Packet estimate in tokens: 783
T0 included at about 37 tokens across 1 files
T1 included at about 89 tokens across 1 files
T2 included at about 214 tokens across 1 files
T3 included at about 240 tokens across 1 files
No tier was dropped.

Completeness check passed. A separate recount of files, statuses, old paths, hunks and lines matches the manifest.
