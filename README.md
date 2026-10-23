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

The same folder works as a plugin payload when it sits inside a plugin tree, because the skill format is the payload either way. The extractor needs Python 3.10 or newer and git, and pull request mode also needs the GitHub CLI. There are no third party dependencies.

## Usage

Extract a pull request by number. The base and head are resolved with the GitHub CLI and the extraction itself runs on local git objects. Both refs must already live in the local clone. When either one is missing the run stops and says to fetch it, because guessing from a same named local branch would build a packet for the wrong change.

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

Re-review after new commits land. The since ref is a re-review input that rides along with any mode, and the packet gains a section with the new commits and a range diff against the previous series. Pass a findings file and the section also marks each prior finding addressed or unaddressed. The findings file holds one finding per line in the form `path:line: text`.

```bash
python3 skills/recognitio/scripts/extract.py --range main...feature --since OLDHEAD --findings findings.txt --out packet --repo .
```

Set a token budget on a large change. The budget is an approximate token count taken as characters divided by four, and the accounting covers the whole packet, header and notes and re-review section included.

```bash
python3 skills/recognitio/scripts/extract.py --range main...feature --budget 60000 --out packet --repo .
```

Choose tiers directly when a review only needs part of the packet. Triage and the change always stay in.

```bash
python3 skills/recognitio/scripts/extract.py --range main...feature --tiers 0-1 --out packet --repo .
```

A run that builds a packet writes two files into the output directory. The packet file is the reading document, and its title calls it the pericope for the change. The manifest file is the receipt, with the resolved refs, the command that produced it, the per file record, the tier accounting, the section headings the packet carries, and the verified flag. A run that fails, at argument checking or later, removes any earlier packet from the directory first and leaves a manifest whose verified flag is false, so a stale packet can never stand as the result of the latest run, as long as the run named an output directory.

The script at `scripts/check_packet.py` validates a packet directory before a review is stamped on it. It confirms the manifest is verified, that the head it records is still the head of the repository under review, and that the sections the manifest records are present and filled in the packet.

## The tier model

The packet is built in four tiers.

- T0 is triage, with the pull request title, body and spec references when the mode resolves them, the file list, the numstat summary, and the commit list for the range.
- T1 is the change, with per file diffs that carry whole enclosing function context instead of a fixed line radius.
- T2 is the companions, with call sites of the changed function names elsewhere in the repo, the imports of each changed file, definitions of the changed names outside the changed files, and test files that mention the changed modules. Companions come from deterministic search only, each one is capped, and the packet says when a cap was hit.
- T3 is history, with a blame summary for the changed ranges in the most changed files, the recent evolution of up to three changed functions, and prior pull requests touching the most changed files when the GitHub CLI can name them. That lookup checks the three most changed files against the thirty most recent pull requests and shows at most five matches, and the packet states that window where it reports the results. When the CLI cannot name them, the tier says so.

Some files stand in the change as named placeholders rather than diffs. A binary file is named with its byte count. A file detected as generated or as a lockfile is named with its detection reason, and detection works from a list of known lockfile names, known generated suffixes, and the do not edit marker in a file header. The header marker withholds a diff only when it already stood at the base revision. A marker that arrives in the change itself is flagged in the packet header and the change is shown in full, because a file cannot exempt itself with words it just wrote. Every placeholder keeps its lines and hunks counted in the manifest, and the packet header lists each one with its reason. A text file that the tree marks binary through its attributes file is counted and shown as text instead, and the header names that too.

A budget spends itself in tier order. T3 drops first and T2 drops second, and the manifest records every drop with its reason. The receipt reports tokens per tier, files per tier, and what was cut. Files per tier counts what each tier worked over. T0 and T1 count every changed file, T2 counts the changed source files it searched for companions, and T3 counts the capped subset of most changed files it drew history from. The change itself never drops and never truncates. When T0 and T1 alone exceed the budget, the run fails with a clear message instead of handing over a partial change dressed as a whole one.

## The completeness guarantee

After assembly, the extractor recounts the changed files, their statuses, their old paths, their hunks, and their added and deleted lines with separate git invocations and compares the recount against the manifest. A disagreement writes a manifest whose verified flag is false, prints the discrepancy, and exits nonzero. A packet that failed its check must never be reviewed as if it were whole. Silence about a missing file is the one failure this project exists to prevent.

Two guards stand in front of the recount. Every git invocation runs with its output format pinned, so configuration in the clone or in a global config file cannot reshape the diff, and path data moves through NUL delimited output, so names with spaces, quotes, or non ASCII characters survive end to end. Packet text preserves the bytes of the change, CRLF line endings included. A shallow clone is refused before any of this runs, because its truncated history cannot support the guarantee.

## The name

Recognitio is a Latin word for a formal re-examination of a matter with the record open. Roman law used it when a case was looked at again by someone charged with getting it right. A pull request review is the same act in modern dress, and the packet this skill builds is the record the examination runs on.
