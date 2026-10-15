# Recognitio

Recognitio is an agent skill that pulls the relevant changes out of a pull request or a commit range and assembles them into a verified review packet. The packet holds the change plus the context a careful human reviewer would go and find, and it proves that nothing was left behind.

## Why

A diff alone is not what a reviewer reads. A reviewer reads the change inside its enclosing function, follows changed names to the places that call them, opens the tests that touch the changed module, and checks who shaped these lines in the past. Most tools hand the reviewer a fixed slice of lines and stay silent when the slice runs out. Hosted diff endpoints cap their file counts and drop oversized patches without a flag, so a large pull request can be reviewed in part while everyone believes it was reviewed in whole.

Recognitio takes the other path. Extraction runs against the local clone, where there is no file count cap and the full history is present. The result is counted twice by separate git invocations, and the packet is only called verified when both counts agree.

## Install

Copy the skill folder into any skills directory your agent reads.

```bash
cp -r skills/recognitio ~/.claude/skills/recognitio
```

The same folder works as a plugin payload when it sits inside a plugin tree, because the skill format is the payload either way. The extractor needs Python 3 and git, and pull request mode also needs the GitHub CLI. There are no third party dependencies.

## Usage

Extract a pull request by number. The base and head are resolved with the GitHub CLI and the extraction itself runs on local git objects.

```bash
python3 skills/recognitio/scripts/extract.py --pr 123 --out packet --repo .
```

Extract a commit range. Both spellings work and both use merge base semantics, so the packet shows what the head proposes rather than drift from the base branch.

```bash
python3 skills/recognitio/scripts/extract.py --range main...feature --out packet --repo .
python3 skills/recognitio/scripts/extract.py --range main..feature --out packet --repo .
```

Extract a single commit against its parent.

```bash
python3 skills/recognitio/scripts/extract.py --commit HEAD --out packet --repo .
```

Re-review after new commits land. The since ref names the head that was reviewed last time, and the packet gains a section with the new commits and a range diff against the previous series.

```bash
python3 skills/recognitio/scripts/extract.py --range main...feature --since OLDHEAD --out packet --repo .
```

Set a token budget on a large change. The budget is an approximate token count taken as characters divided by four.

```bash
python3 skills/recognitio/scripts/extract.py --range main...feature --budget 60000 --out packet --repo .
```

Every run writes two files into the output directory. The packet file is the reading document, and its title calls it the pericope for the change. The manifest file is the receipt, with the resolved refs, the per file record, the tier accounting, and the verified flag.

## The tier model

The packet is built in four tiers.

- T0 is triage, with the numstat summary and the commit list for the range.
- T1 is the change, with per file diffs that carry whole enclosing function context instead of a fixed line radius.
- T2 is the companions, with call sites of the changed function names elsewhere in the repo and test files that mention the changed modules. Companions come from deterministic search only, each one is capped, and the packet says when a cap was hit.
- T3 is history, with a blame summary for the changed ranges in the most changed files and the recent evolution of up to three changed functions.

A budget spends itself in tier order. T3 drops first and T2 drops second, and the manifest records every drop with its reason. The change itself never drops and never truncates. When T0 and T1 alone exceed the budget, the run fails with a clear message instead of handing over a partial change dressed as a whole one.

## The completeness guarantee

After assembly, the extractor recounts the changed files, their statuses, and their hunks with separate git invocations and compares the recount against the manifest. A disagreement writes a manifest whose verified flag is false, prints the discrepancy, and exits nonzero. A packet that failed its check must never be reviewed as if it were whole. Silence about a missing file is the one failure this project exists to prevent.

## The name

Recognitio is a Latin word for a formal re-examination of a matter with the record open. Roman law used it when a case was looked at again by someone charged with getting it right. A pull request review is the same act in modern dress, and the packet this skill builds is the record the examination runs on.
