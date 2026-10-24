---
name: recognitio
description: Extracts the changes from a pull request, a commit range, or a single commit and assembles them with their surrounding context into one verified packet, so a review can start from evidence instead of a bare diff. Use it when someone asks to extract changes, pull a diff for review, prepare a review packet, re-review a change after new commits, or confirm that everything in a change is present before review begins. The skill assembles evidence only. It does not conduct the review itself, judge whether a change is safe to merge, or fix findings.
context: fork
background: false
---

# Recognitio

## Purpose

Recognitio assembles what a reviewer reads. It takes a pull request, a commit range, or a single commit and builds one packet that holds the change together with the context a careful human reviewer would go and find. It makes no judgement about the code. Judgement belongs to the review skill that reads the packet.

A raw diff is not what a reviewer reads. A reviewer reads the change inside its enclosing function, follows the changed names to their call sites, checks the tests that touch the changed module, and looks at who shaped these lines before. Recognitio gathers all of that ahead of time, counts it, and proves that nothing is missing.

## Input modes

Every run uses one of three input modes. A since ref can ride along with any of them for re-review, and it is an input to a mode rather than a mode of its own.

- Pull request mode takes a PR number and resolves the base and head with the GitHub CLI. Both refs must already live in the local clone. When either ref is missing the run stops with an error and says to fetch it, because a same named local branch is not evidence of the pull request head.
- Range mode takes two refs in the form A..B or A...B and extracts what the second ref proposes against their merge base.
- Commit mode takes one commit and extracts that commit against its parent. A root commit extracts against the empty tree and its manifest records no merge base.

Extraction always runs against the local clone. The hosted API diff is never trusted, because hosted diffs cap out and drop files without saying so. Local git has no file count cap and holds the full history. A shallow clone is refused outright, because truncated history would let the packet describe a boundary commit as the whole tree.

## Workflow

Follow these steps in order.

1. Resolve the refs and confirm that the base, the head, and the merge base all resolve in the local clone. Stop and report the problem when a ref does not resolve.
2. Choose the tiers and a budget for the size of the change, following the guidance below.
3. Run the bundled extractor script with the chosen mode, an output directory, and the tier and budget choices from the step above.
4. Read the manifest the script writes and check that its verified flag is true before anything else happens. Where the repo carries the packet check script, run it against the packet directory as the mechanical form of this step.
5. Hand the packet to the review skill when verification passed. Stop and say exactly what is missing when verification failed.
6. Record the base, the head, and the merge base from the manifest wherever the review itself gets recorded, so the review can be reproduced later.

Run the commands from the repository root, where the paths below resolve.

```bash
python3 .agents/skills/recognitio/scripts/extract.py --pr 123 --out packet --repo .
python3 .agents/skills/recognitio/scripts/extract.py --range main...feature --out packet --repo .
python3 .agents/skills/recognitio/scripts/extract.py --commit HEAD --out packet --repo .
python3 .agents/skills/recognitio/scripts/extract.py --range main...feature --since OLDHEAD --findings findings.txt --budget 60000 --out packet --repo .
```

When the host runs this skill in a forked subagent, the return to the main conversation carries only the packet directory, the manifest's verified flag, and the base, head, and merge base refs. The reviewer opens the packet file itself for the evidence and never works from a reprinted copy.

## Choosing tiers

Size decides the packet shape.

- A small change gets every tier and no budget. Read the whole packet.
- A medium change gets every tier and a budget sized to the reading. The budget sheds history before companions, and the packet records what it shed.
- A large change gets a tier selection. Run once with `--tiers 0-1` for triage and the change, then run again per area of the change with the companion and history tiers where the review needs depth.
- A change whose core tiers alone exceed the budget is too large for one packet. Split the review by directory or by module instead of raising the budget until the packet is unreadable.

## Fanning out

A packet fans out by file or by module. Each review lane takes its slice of the change tier plus the companion and history entries for the same files, and lanes never share a slice. A verifier lane re-reads the cited slices against the manifest before findings are gathered, so a finding that rests on a line the packet does not hold is caught as a packet defect rather than shipped as a review comment.

## Escalation

Raise a tier when the evidence runs out. When a call site in the companion tier shows a caller the packet did not gather context for, re-run with the history tier added or with a wider budget and say in the gate report that the first packet was thin. When verification fails, escalation is forbidden until the failure is explained. A failed packet is a stop, not a smaller yes.

## Stamping the gate report

A review is stamped only on a verified packet. The gate report records the base, the head, and the merge base from the manifest, the exact extractor command, and the reviewed head. Run the packet check script against the packet directory when the working repo carries one. It confirms the manifest is verified, that its recorded head is still the head being reviewed, and that the sections the manifest records are present and filled in the packet, which is the guard against stamping a review on stale or thin evidence.

## The tier model

The packet is built in tiers and each tier is a named section of the packet.

- T0 holds triage. It carries the pull request title, body, and spec references when the mode resolves them, the file list, the numstat summary, and the commit list for the range, so a reviewer sees why the change exists and what shape it has before its content. A changed file whose name marks it as an instruction bearing file is flagged as an instruction file in the file list, and its record in the manifest carries the same flag as a boolean named instruction_file. The name set is AGENTS.md and CLAUDE.md and SKILL.md and GEMINI.md at any depth, the Copilot instructions file name, a path specific Copilot instructions file under the instructions folder of .github carrying the .instructions.md suffix, the .cursorrules file name, a Cursor rules file under a .cursor folder, and a Claude rules file under a .claude/rules folder. A Kimi
plugin manifest named kimi.plugin.json at any depth, a Kimi plugin
agent or hook script under a .kimi-plugin folder, and a Kimi
plugin manifest under a .kimi-plugin folder are flagged too,
because a change to any of them steers the next agent that loads
the tree. A renamed file is flagged when either its old name or its new name stands in the set, because a change to such a file steers the next agent that loads the tree. A review packet output style under the output-styles folder of the plugin is flagged too, because it steers the next agent that loads the tree.
- T1 holds the change itself. It carries the per file diffs with whole enclosing function context, so every edited line is read inside the function it lives in. Binary files and detected generated files and lockfiles stand as named placeholders here, counted in full in the manifest and named in the packet header. A generated file marker withholds a diff only when the marker already stood at the base revision. A marker that arrives in the change is flagged in the header and the change is shown in full. A file that changed from binary content to text in the change is counted and shown as text, and its header receipt names the transition rather than any attribute marking.
- T2 holds the companions. It carries call sites for the changed function names elsewhere in the repo, the imports of each changed file, definitions of the changed names outside the changed files, and the test files that mention the changed modules, all found by deterministic search and capped with the caps stated in the packet. One bulk search over the tree gathers every term the tier needs, so the gathering cost stays with the size of the tree and the change rather than growing with their product. The bulk search hands each line only to the terms it word matches under the same boundary rule the per term search uses, at both ends of the term whatever characters the term begins or ends with. In the test files section one line is one piece of evidence however many terms match it, and the hits are deduped by file and line before the cap applies, so the cap and its note count distinct lines. A module that was renamed in the change is searched under its old name as well as its new one, so a test file that still mentions the module under the name it carried before the change is found and named. A companion search that fails ends the run with a failure receipt rather than reporting that nothing was found. The search is line based and pattern based, so a definition split across lines or written in a language outside the five the patterns know will not be found, and the packet says only what the search found.
- T3 holds history. It carries a blame summary for the changed ranges in the most changed files, the recent evolution of up to three changed functions, and prior pull requests touching the most changed files when the GitHub CLI can name them. That lookup checks the three most changed files against the thirty most recent pull requests and shows at most five matches, and the packet states the window where it reports. When the CLI cannot name them, the tier says so instead of staying silent.

A token budget spends itself in tier order and the accounting covers the whole packet, header and notes and re-review section included. When a packet runs over budget, T3 drops first and T2 drops second, and the packet records what was dropped and why. T0 and T1 never drop and never truncate. When T0 and T1 alone exceed the budget, the script exits with an error and no packet is presented as ready. A tier selection is a separate control. It chooses which of the companion and history tiers are built at all, and the budget can only shed tiers the selection kept.

## Completeness discipline

The completeness check is the heart of this skill. After the packet is assembled, the script recounts the changed files, their statuses, their old paths, their hunks, and their added and deleted lines with separate git invocations and compares the recount against the manifest. Any disagreement sets the verified flag to false and the script exits nonzero with the discrepancy printed.

Never present a partial packet as a complete one. Never let a review begin on a packet whose verified flag is false. When verification fails, stop and say what is missing in plain words, naming the files or hunks that disagree. A smaller packet that passed its check is worth more than a larger one that was never counted.

A path that carries a newline or another control character is escaped wherever the packet names the file, so a crafted name cannot print a forged section in the packet voice.

A failed run never leaves an earlier packet standing in the output directory. The run removes the old packet and manifest first and leaves a manifest whose verified flag is false, so whatever a reader finds in the directory belongs to the latest run.

## Re-review

Re-review uses the since ref, which names the head that was reviewed last time. The packet still covers the whole change and gains a re-review section with the commits that arrived since then and a range diff between the old series and the new one. Reviewers read the re-review section first and the full tiers when they need the wider picture. This is also the right tool after a rebase, because the range diff shows whether hunks survived the move.

Pass the prior findings with `--findings` and the packet marks each one addressed or unaddressed. The findings file holds one finding per line in the form `path:line: text`. A finding counts as addressed when its file is gone at the head or when the lines it anchors to changed between the previous head and this one, and as unaddressed when those lines survived untouched. A change of line endings alone does not count as a change to an anchored line, so a rename that only re-terminates a file leaves the findings on its unchanged lines unaddressed. A finding whose path did not exist at the previous reviewed revision counts as unaddressed and the accounting says so, because no anchored line was reviewed then. A finding whose path existed at the previous reviewed revision and whose file is gone at the head counts as addressed. Repeated copies of one finding are removed before the cap is applied and the section states how many were removed, so duplicates count once and cannot crowd a distinct finding past the cap. A path written with a leading ./ is accounted under its plain spelling, so the same finding written both ways also counts once and carries one verdict. The same accounting covers a dot segment standing in the middle of a path, a doubled separator, a backslash used as a separator, stray space standing before the anchor colon, and a path written in decomposed Unicode form, and each of those spellings is accounted under the one plain composed spelling of the file it names. Case is never folded, because two spellings that differ only in case can name two different files in one tree. The accounting covers at most one hundred findings and says so in the section when a file carries more, and a findings file that holds none is reported as empty rather than passed over in silence.

When the since ref shares no history with the change, the re-review section says so and stays empty of commits and diffs. An unrelated since ref is a mistake to surface, not a series to summarise.

## Trust and limits

Extraction is local only, and nothing in this skill points at an untrusted network source. A verified packet proves the packet is complete. It does not prove the change is correct or safe. Run the packet check script before a packet is trusted, as step 4 of the workflow already orders.

## The boundary

Recognitio assembles what reviewers read and proves the assembly is whole. It does not approve, reject, rank, or comment on the code. Those acts belong to the review skill downstream, which keeps its own axes and its own reporting rules. When a review finds nothing where evidence should have been, check the packet first and the reviewer second, because the split between extraction and judgement is what makes either side auditable.
