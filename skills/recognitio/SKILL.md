---
name: recognitio
description: Extracts the relevant changes from a pull request, a PR, a commit range, or a single commit and assembles them with their surrounding context into a verified review packet for code review. Use it when someone asks to extract changes, pull a diff for review, prepare a review packet, re-review a change after new commits, or confirm that everything in a change is present before review begins.
---

# Recognitio

## Purpose

Recognitio assembles what a reviewer reads. It takes a pull request, a commit range, or a single commit and builds one packet that holds the change together with the context a careful human reviewer would go and find. It makes no judgement about the code. Judgement belongs to the review skill that reads the packet.

A raw diff is not what a reviewer reads. A reviewer reads the change inside its enclosing function, follows the changed names to their call sites, checks the tests that touch the changed module, and looks at who shaped these lines before. Recognitio gathers all of that ahead of time, counts it, and proves that nothing is missing.

## Input modes

Recognitio has four input modes and every run uses one of them.

- Pull request mode takes a PR number, resolves the base and head in the local clone with the GitHub CLI, and extracts from local git objects.
- Range mode takes two refs in the form A..B or A...B and extracts what the second ref proposes against their merge base.
- Commit mode takes one commit and extracts that commit against its parent.
- Re-review mode adds a since ref to any of the other modes and the packet gains a section that shows only what moved since the previous review.

Extraction always runs against the local clone. The hosted API diff is never trusted, because hosted diffs cap out and drop files without saying so. Local git has no file count cap and holds the full history.

## Workflow

Follow these steps in order.

1. Resolve the refs and confirm that the base, the head, and the merge base all resolve in the local clone. Stop and report the problem when a ref does not resolve.
2. Run the bundled extractor script with the chosen mode, an output directory, and a token budget when the change is large.
3. Read the manifest the script writes and check that its verified flag is true before anything else happens.
4. Hand the packet to the review skill when verification passed. Stop and say exactly what is missing when verification failed.
5. Record the base, the head, and the merge base from the manifest wherever the review itself gets recorded, so the review can be reproduced later.

```bash
python3 scripts/extract.py --pr 123 --out packet --repo .
python3 scripts/extract.py --range main...feature --out packet --repo .
python3 scripts/extract.py --commit HEAD --out packet --repo .
python3 scripts/extract.py --range main...feature --since OLDHEAD --budget 60000 --out packet --repo .
```

## The tier model

The packet is built in tiers and each tier is a named section of the packet.

- T0 holds triage. It carries the numstat summary and the commit list for the range, so a reviewer sees the shape of the change before its content.
- T1 holds the change itself. It carries the per file diffs with whole enclosing function context, so every edited line is read inside the function it lives in.
- T2 holds the companions. It carries call sites for the changed function names elsewhere in the repo and the test files that mention the changed modules, all found by deterministic search and capped with the caps stated in the packet.
- T3 holds history. It carries a blame summary for the changed ranges in the most changed files and the recent evolution of up to three changed functions.

A token budget spends itself in tier order. When a packet runs over budget, T3 drops first and T2 drops second, and the packet records what was dropped and why. T0 and T1 never drop and never truncate. When T0 and T1 alone exceed the budget, the script exits with an error and no packet is presented as ready.

## Completeness discipline

The completeness check is the heart of this skill. After the packet is assembled, the script recounts the changed files, their statuses, and their hunks with separate git invocations and compares the recount against the manifest. Any disagreement sets the verified flag to false and the script exits nonzero with the discrepancy printed.

Never present a partial packet as a complete one. Never let a review begin on a packet whose verified flag is false. When verification fails, stop and say what is missing in plain words, naming the files or hunks that disagree. A smaller packet that passed its check is worth more than a larger one that was never counted.

## Re-review

Re-review uses the since ref, which names the head that was reviewed last time. The packet still covers the whole change and gains a re-review section with the commits that arrived since then and a range diff between the old series and the new one. Reviewers read the re-review section first and the full tiers when they need the wider picture. This is also the right tool after a rebase, because the range diff shows whether hunks survived the move.

## The boundary

Recognitio assembles what reviewers read and proves the assembly is whole. It does not approve, reject, rank, or comment on the code. Those acts belong to the review skill downstream, which keeps its own axes and its own reporting rules. When a review finds nothing where evidence should have been, check the packet first and the reviewer second, because the split between extraction and judgement is what makes either side auditable.
