# The pericope for commit 991ac6ae80d3

A recognitio review packet. The pericope named in the title is this packet, holding the change and the context a reviewer needs to read it, and nothing else.

Mode: commit

Base: eba549658f9c21e78115f6caf96034dd142af4e6

Head: 991ac6ae80d3c00c0b6c7fc06a4a35bdafb2d965

Merge base: eba549658f9c21e78115f6caf96034dd142af4e6

Verified: yes. The recount at the close of this packet carries the proof.

Contents

This packet holds 2 files, 2 hunks, 24 added lines and 0 deleted lines

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

- scripts/check_antigravity.py (modified)
- scripts/check_devin.py (modified)

### Numstat

```
14	0	scripts/check_antigravity.py
10	0	scripts/check_devin.py
```

### Commits

```
991ac6a fix: catch membership stated through a pure modifier chain in the Devin gate
```

## T1 The change

Each file shows its diff with whole enclosing function context.

### scripts/check_antigravity.py

Status: modified

```diff
diff --git a/scripts/check_antigravity.py b/scripts/check_antigravity.py
old mode 100755
new mode 100644
index 8b92bee..a95e882
--- a/scripts/check_antigravity.py
+++ b/scripts/check_antigravity.py
@@ -69,92 +69,106 @@ PRIMARY_CITATIONS = (
 # Brief sentences the gate pins. Each is a fragment of the exact
 # sentence the brief carries, so a later edit that softens or
 # drops a stated pin, quote, date, or limit fails loudly.
 PINNED = (
     ("the primary read date",
      "per the primary Google docs read as text on 2026-10-24"),
     ("the required plugin.json marker",
      "`plugin.json` as the required marker"),
     ("the six hook events",
      "`SessionStart`, `PreToolUse`, `PostToolUse`, `PreInvocation`, "
      "`PostInvocation`, and `Stop`"),
     ("the three hook decisions",
      "This build's hook uses three of them, `deny`, `force_ask`, "
      "and `auto_approve`"),
     ("the sunset halt",
      "Starting October 9 2026, no new Gemini Code Assist Standard "
      "or Enterprise subscriptions can be purchased"),
     ("the contract terms",
      "Existing subscriptions continue through their contract terms"),
     ("the renewal dates",
      "License additions and annual renewals run to January 31 2027"),
     ("the named path",
      "The page names Antigravity as the forward path for agentic "
      "coding assistance"),
     ("the migration guide",
      "The page's FAQ names the Gemini CLI to Antigravity CLI "
      "migration guide"),
     ("the no stamp discipline",
      "this brief never pins a page stamp, because a stamp is a "
      "moving target"),
     ("the sunset read date",
      "The round 24 lane read the sunset page live on 2026-10-24"),
+    ("the GitHub split form",
+     "The Gemini Code Assist service on GitHub stands in split "
+     "form"),
+    ("the GitHub consumer deprecation",
+     "the consumer version deprecated on June 18 2026"),
+    ("the GitHub consumer shutdown",
+     "shut down on July 17 2026"),
+    ("the GitHub enterprise unaffected",
+     "the enterprise version not affected"),
+    ("the config page posture",
+     "No brief cites the config page as proof of consumer "
+     "availability"),
+    ("the enterprise status check",
+     "requires a current primary status check first"),
     ("the v0.65.0 pin",
      "v0.65.0 is the stable pin for the Gemini CLI extension bundle"),
     ("the docs lag",
      "the brief trusts the releases page over the docs page"),
     ("the pre-release",
      "it is not stable, so the v0.65.0 pin stands"),
     ("the frontmatter watch",
      "the change stays an adjacent watch item with no brief impact"),
     ("the extension boundary",
      "The Antigravity native shapes live as a second extensions "
      "namespace beside the portable core, never blended into it"),
     ("the no primary namespace",
      "No primary source names a reverse domain namespace for an "
      "Antigravity plugin"),
     ("the namespace placeholder",
      "the portable manifest uses `com.google.antigravity` as a "
      "documented placeholder"),
     ("the not primary",
      "the brief does not present it as primary"),
     ("the declared paths",
      "the gate resolves every declared path in the repo"),
     ("the skills folder rule",
      "every skill lives inside the plugin's `skills` folder"),
     ("the no second skill copy",
      "so the build ships no second skill copy"),
     ("the Antigravity first orientation",
      "which confirms the Antigravity first orientation the program "
      "already carried"),
     ("the stdin stdout contract",
      "receives the event JSON on stdin and returns a JSON object "
      "on stdout"),
     ("the deny mapping",
      "`deny` refuses the tool call with a reason when the packet "
      "manifest is missing or not verified"),
     ("the force_ask mapping",
      "`force_ask` holds the tool call for user confirmation when "
      "the packet manifest is unreadable or unparsable"),
     ("the auto_approve mapping",
      "`auto_approve` lets the tool call through without asking when "
      "the packet manifest reads verified"),
     ("the degraded state",
      "A missing or unparseable hook file is a planned degraded "
      "state, never a silent pass"),
     ("the host fallback",
      "the review run falls back to the shipped scripts"),
     ("the Claude Code only negative",
      "The Build 7 mod hooks are Claude Code only on current "
      "evidence"),
     ("the honest limit",
      "the brief claims no product enforcement behavior it cannot "
      "run"),
     ("the four frontmatter keys",
      "The canonical skill frontmatter holds exactly four keys, "
      "name, description, context, and background"),
     ("the second packet guard",
      "A statement with neither is a rival instruction source and "
      "fails the round"),
     ("the decision 4 statement",
      "Decision 4 binds this build like every other build"),
 )
```

### scripts/check_devin.py

Status: modified

```diff
diff --git a/scripts/check_devin.py b/scripts/check_devin.py
index 0327324..522392d 100644
--- a/scripts/check_devin.py
+++ b/scripts/check_devin.py
@@ -421,163 +421,173 @@ def naming_problems(root=None):
 def semantic_problems(root=None):
     """R32-RT-01. No sentence may contradict the resolved count,
     the bypass surface, or the SARIF export shape.
 
     The pins prove the correct sentences are stated, but an
     added sentence or an in place rewrite passes while the
     pins stay in place, because no check reads the
     contradicting sentence. This check reads every sentence
     in the whole brief, inside and outside the rules
     section, so an appended rule contradicts just as loudly
     as an in rule rewrite. Sentences that state the correct
     posture with a negation, such as dismissed findings no
     longer counting, the bypass path never assumed absent,
     or CSV alone never named as the export shape, are
     skipped.
     """
     root = ROOT if root is None else root
     raw = read_text(root / "docs" / "devin-playbook-brief.md")
     if raw is None:
         return ["docs/devin-playbook-brief.md is missing"]
     sentences = [
         sentence.strip()
         for sentence in re.split(
             r"(?<=[.!?])\s+", re.sub(r"\s+", " ", raw)
         )
         if sentence.strip()
     ]
     problems = []
     seen = set()
     for sentence in sentences:
         low = sentence.lower()
         negated = bool(
             re.search(r"\b(no longer|never)\b", low)
             or re.search(r"\bnot\b.{0,20}\bcount\w*\b", low)
         )
         if "resolved" not in seen and not negated and (
             re.search(r"\bdismissed\b.{0,50}\bcount\w*\b", low)
             or re.search(
                 r"\bresolved\b.{0,30}\bincludes?\b.{0,30}"
                 r"\bdismissed\b",
                 low,
             )
         ):
             problems.append(RESOLVED_PROBLEM)
             seen.add("resolved")
         correct_definition = bool(
             re.search(
                 r"\b(excluded|only when|fixed in code|code fixed only)\b",
                 low,
             )
         )
         if (
             "resolved" not in seen
             and not negated
             and not correct_definition
             and (
                 re.search(
                     r"\bresolved\b.{0,60}\bcount\w*\b.{0,40}"
                     r"\bdismissed\b",
                     low,
                 )
                 or re.search(
                     r"\bcount\w*\b.{0,60}\bresolved\b.{0,40}"
                     r"\bdismissed\b",
                     low,
                 )
             )
         ):
             problems.append(RESOLVED_PROBLEM)
             seen.add("resolved")
         verb_then_equivalence = bool(re.search(
             r"\b(" + RESOLVED_VERBS + r")\b.{0,80}\b("
             + EQUIVALENCE_PHRASES + r")\b",
             low,
         ))
         membership_near_resolved = bool(re.search(
             r"\b(" + MEMBERSHIP_PHRASES + r")\b.{0,15}\bresolved\b",
             low,
         ))
+        # Modifier chain from R36-E1-02. A membership phrase
+        # followed by a pure modifier chain and then
+        # resolved states the same membership at any gap
+        # length, so it fires beside the bounded form.
+        membership_modifier_chain = bool(re.search(
+            r"\b(" + MEMBERSHIP_PHRASES + r")\b"
+            + MEMBERSHIP_MODIFIER_GAP + r"resolved\b",
+            low,
+        ))
         # Verb plus membership from S4. A listed verb within
         # 30 of a membership phrase with resolved within 20
         # of the phrase restores the long filler verb shape.
         # The 19 filler comprehensive shape fires while the
         # 21 filler audit trail shape stays out, and a probe
         # with no listed verb stays out on the verb test
         # alone even before the bounds are reached.
         verb_then_membership_near_resolved = bool(re.search(
             r"\b(" + RESOLVED_VERBS + r")\b.{0,30}\b("
             + MEMBERSHIP_PHRASES + r")\b.{0,20}\bresolved\b",
             low,
         ))
         if (
             "resolved" not in seen
             and not negated
             and not correct_definition
             and "dismissed" in low
             and "resolved" in low
             and (
                 verb_then_equivalence
                 or membership_near_resolved
+                or membership_modifier_chain
                 or verb_then_membership_near_resolved
             )
         ):
             problems.append(RESOLVED_PROBLEM)
             seen.add("resolved")
         if "bypass" not in seen and (
             re.search(r"without (any )?bypass", low)
             or re.search(r"\bno bypass\b", low)
             or (
                 "assume" not in low
                 and re.search(
                     r"\bbypass (surface|path)\b.{0,20}\babsent\b",
                     low,
                 )
             )
             or re.search(
                 r"\bbypass\b.{0,20}\b(not needed|not required"
                 r"|unnecessary)\b",
                 low,
             )
         ):
             problems.append(
                 "a devin rule merges a blocked pull request "
                 "without a bypass surface, which the merge past "
                 "bypass surface forbids"
             )
             seen.add("bypass")
         if "sarif" not in seen and (
             re.search(r"\bcsv only\b", low)
             or (not negated and re.search(r"\bcsv alone\b", low))
             or re.search(
                 r"\bsarif\b.{0,30}\b(dropped|removed|absent)\b",
                 low,
             )
             or re.search(r"without sarif", low)
         ):
             problems.append(
                 "a devin rule exports CSV only, which the SARIF "
                 "2.1.0 export beside CSV forbids"
             )
             seen.add("sarif")
         if "sarif" not in seen and "sarif" in low:
             versions = re.findall(r"\b\d+\.\d+(?:\.\d+)?\b", low)
             if any(version != "2.1.0" for version in versions):
                 problems.append(SARIF_PROBLEM)
                 seen.add("sarif")
         if "sarif" not in seen and "sarif" in low:
             # Bare version from R-06, with an optional v prefix.
             # The lookahead still lets the full 2.1.0 pin pass,
             # because its 2 is followed by a dot digit.
             bare = re.search(
                 r"\bsarif(?:\s+version)?\s*v?(\d+)(?!\.\d)", low
             )
             if bare:
                 problems.append(SARIF_PROBLEM)
                 seen.add("sarif")
         if "sarif" not in seen and "sarif" in low:
             # Spelled version from W-07, checked after the
             # digit blocks so a digit pin still decides first.
             if spelled_sarif_problem(low):
                 problems.append(SARIF_PROBLEM)
                 seen.add("sarif")
     return problems
```

## T2 Companions

Call sites, imports, definitions and test files found by deterministic search at the head revision.

### Call sites for naming_problems in scripts/check_devin.py

No call sites found outside the changed file.

### Call sites for semantic_problems in scripts/check_devin.py

No call sites found outside the changed file.

### Imports of the changed files

#### scripts/check_antigravity.py

```
28: import json
29: import re
30: import sys
31: from pathlib import Path
```

#### scripts/check_devin.py

```
31: import re
32: import sys
33: from pathlib import Path
```

### Definitions of changed names elsewhere

No definitions of the changed names were found outside the changed files.

### Test files that mention the changed code

#### tests/test_antigravity.py

```
47:         self.mod = load_script("check_antigravity")
```

#### tests/test_devin.py

```
20: at scripts/check_devin.py. These tests prove the pin fires
50:         self.mod = load_script("check_devin")
```

## T3 History

### Blame summary for changed ranges

#### scripts/check_antigravity.py

```
David Engelmann 991ac6ae lines 14
```

#### scripts/check_devin.py

```
David Engelmann 991ac6ae lines 10
```

### Recent evolution of changed functions

#### naming_problems in scripts/check_devin.py

```
commit 1c99083 fix: land Build 17 Devin, harden Kimi and Copilot gates against replacement rewording, and fold the round 30 corrections

diff --git a/scripts/check_devin.py b/scripts/check_devin.py
--- /dev/null
+++ b/scripts/check_devin.py
@@ -0,0 +271,31 @@
+def naming_problems(root=None):
+    """Problems with the Devin Dynamic Workflows naming guard.
+
+    Every Devin Dynamic Workflows mention must name Devin, so
+    the Build 6 Claude Code fan out surface is never confused
+    with Devin Dynamic Workflows, and the brief must never cite
+    the Build 6 figures as evidence about Devin.
+    """
+    root = ROOT if root is None else root
+    raw = read_text(root / "docs" / "devin-playbook-brief.md")
+    if raw is None:
+        return ["docs/devin-playbook-brief.md is missing"]
+    flat = re.sub(r"\s+", " ", raw).lower()
+    problems = []
+    for match in re.finditer(r"dynamic workflows", flat):
+        before = flat[max(0, match.start() - 6):match.start()]
+        if before != "devin ":
+            problems.append(
+                "docs/devin-playbook-brief.md names dynamic "
+                "workflows without Devin, which confuses the "
+                "Build 6 surface with Devin Dynamic Workflows"
+            )
+            break
+    if "16 agents" in flat:
+        problems.append(
+            "docs/devin-playbook-brief.md cites the Build 6 "
+            "figures as evidence about Devin"
+        )
+    return problems
+
+
```

#### semantic_problems in scripts/check_devin.py

```
commit 991ac6a fix: catch membership stated through a pure modifier chain in the Devin gate

diff --git a/scripts/check_devin.py b/scripts/check_devin.py
--- a/scripts/check_devin.py
+++ b/scripts/check_devin.py
@@ -421,165 +421,175 @@
 def semantic_problems(root=None):
     """R32-RT-01. No sentence may contradict the resolved count,
     the bypass surface, or the SARIF export shape.
 
     The pins prove the correct sentences are stated, but an
     added sentence or an in place rewrite passes while the
     pins stay in place, because no check reads the
     contradicting sentence. This check reads every sentence
     in the whole brief, inside and outside the rules
     section, so an appended rule contradicts just as loudly
     as an in rule rewrite. Sentences that state the correct
     posture with a negation, such as dismissed findings no
     longer counting, the bypass path never assumed absent,
     or CSV alone never named as the export shape, are
     skipped.
     """
     root = ROOT if root is None else root
     raw = read_text(root / "docs" / "devin-playbook-brief.md")
     if raw is None:
         return ["docs/devin-playbook-brief.md is missing"]
     sentences = [
         sentence.strip()
         for sentence in re.split(
             r"(?<=[.!?])\s+", re.sub(r"\s+", " ", raw)
         )
         if sentence.strip()
     ]
     problems = []
     seen = set()
     for sentence in sentences:
         low = sentence.lower()
         negated = bool(
             re.search(r"\b(no longer|never)\b", low)
             or re.search(r"\bnot\b.{0,20}\bcount\w*\b", low)
         )
         if "resolved" not in seen and not negated and (
             re.search(r"\bdismissed\b.{0,50}\bcount\w*\b", low)
             or re.search(
                 r"\bresolved\b.{0,30}\bincludes?\b.{0,30}"
                 r"\bdismissed\b",
                 low,
             )
         ):
             problems.append(RESOLVED_PROBLEM)
             seen.add("resolved")
         correct_definition = bool(
             re.search(
                 r"\b(excluded|only when|fixed in code|code fixed only)\b",
                 low,
             )
         )
         if (
             "resolved" not in seen
             and not negated
             and not correct_definition
             and (
                 re.search(
                     r"\bresolved\b.{0,60}\bcount\w*\b.{0,40}"
                     r"\bdismissed\b",
                     low,
                 )
                 or re.search(
                     r"\bcount\w*\b.{0,60}\bresolved\b.{0,40}"
                     r"\bdismissed\b",
                     low,
                 )
             )
         ):
             problems.append(RESOLVED_PROBLEM)
             seen.add("resolved")
         verb_then_equivalence = bool(re.search(
             r"\b(" + RESOLVED_VERBS + r")\b.{0,80}\b("
             + EQUIVALENCE_PHRASES + r")\b",
             low,
         ))
         membership_near_resolved = bool(re.search(
             r"\b(" + MEMBERSHIP_PHRASES + r")\b.{0,15}\bresolved\b",
             low,
         ))
+        # Modifier chain from R36-E1-02. A membership phrase
+        # followed by a pure modifier chain and then
+        # resolved states the same membership at any gap
+        # length, so it fires beside the bounded form.
+        membership_modifier_chain = bool(re.search(
+            r"\b(" + MEMBERSHIP_PHRASES + r")\b"
+            + MEMBERSHIP_MODIFIER_GAP + r"resolved\b",
+            low,
+        ))
         # Verb plus membership from S4. A listed verb within
         # 30 of a membership phrase with resolved within 20
         # of the phrase restores the long filler verb shape.
         # The 19 filler comprehensive shape fires while the
         # 21 filler audit trail shape stays out, and a probe
         # with no listed verb stays out on the verb test
         # alone even before the bounds are reached.
         verb_then_membership_near_resolved = bool
```

### Prior pull requests touching these files

Scope of the lookup: the 3 most changed files, checked against the 30 most recent pull requests, with at most 5 matches shown. A pull request outside that window is not reported here.

The states in this list are a snapshot from the fetch that built this packet. They are not refreshed after that fetch and they are not a live claim about any pull request.

Prior pull requests are unavailable in this environment. The GitHub CLI is missing or this clone is not a GitHub checkout, so no pull request history was gathered.

### Cap notes

Cap note: history for semantic_problems capped.

## Verification recount

### Budget

Budget in tokens: none set

Packet estimate in tokens: 5947

T0 included at about 114 tokens across 2 files

T1 included at about 3285 tokens across 2 files

T2 included at about 323 tokens across 2 files

T3 included at about 1789 tokens across 2 files

No tier was dropped.

### Recount

Recount passed

A separate recount counted the change a second time

The recount covered 2 files with their statuses and old paths, 2 hunks, and 24 added lines and 0 deleted lines

The recount matches the manifest on every count

Every tier is included

Verified means this packet holds the whole change it names

Verified does not mean the change is correct or safe
