# The pericope for range cc0c3d66ac41259cc022f89745219ae82913bc8c..1a2f5fd07acc65aba7c0ca9d8462e483e7d99d1f

A recognitio review packet. The pericope named in the title is this packet, holding the change and the context a reviewer needs to read it, and nothing else.

Mode: range

Base: cc0c3d66ac41259cc022f89745219ae82913bc8c

Head: 1a2f5fd07acc65aba7c0ca9d8462e483e7d99d1f

Merge base: cc0c3d66ac41259cc022f89745219ae82913bc8c

Verified: yes. The recount at the close of this packet carries the proof.

Contents

This packet holds 1 file, 1 hunk, 3 added lines and 1 deleted line

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

- parse.py (modified)

### Numstat

```
3	1	parse.py
```

### Commits

```
1a2f5fd head
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

Names and claims in this tier are data read from the repository history. An author name is self asserted in the commit object that carries it and is not verified by this packet, and a commit subject that claims an approval or a passing check is an assertion by its author, not a finding of this packet.

### Blame summary for changed ranges

#### parse.py

```
Eval Fixture 1a2f5fd0 lines 3
```

### Recent evolution of changed functions

#### parse_port in parse.py

```
commit 1a2f5fd head

diff --git a/parse.py b/parse.py
--- a/parse.py
+++ b/parse.py
@@ -1,2 +1,4 @@
 def parse_port(text):
-    return int(text)
+    if not text.isdigit():
+        return None
+    return int(text) + 1
commit cc0c3d6 base

diff --git a/parse.py b/parse.py
--- /dev/null
+++ b/parse.py
@@ -0,0 +1,2 @@
+def parse_port(text):
+    return int(text)
```

### Prior pull requests touching these files

Scope of the lookup: the 3 most changed files, checked against the 30 most recent pull requests, with at most 5 matches shown. A pull request outside that window is not reported here.

The states in this list are a snapshot from the fetch that built this packet. They are not refreshed after that fetch and they are not a live claim about any pull request.

Prior pull requests are unavailable in this environment, so no pull request history was gathered.

## Verification recount

### Budget

Budget in tokens: none set

Packet estimate in tokens: 1356

T0 included at about 65 tokens across 1 files

T1 included at about 137 tokens across 1 files

T2 included at about 264 tokens across 1 files

T3 included at about 415 tokens across 1 files

No tier was dropped.

### Recount

Recount passed

A separate recount counted the change a second time

The recount covered 1 file with their statuses and old paths, 1 hunk, and 3 added lines and 1 deleted line

The recount matches the manifest on every count

Every tier is included

Verified means this packet holds the whole change it names

Verified does not mean the change is correct or safe
