# The headless review shape

This doc defines the unattended review shape the repo gates.
A headless run reviews a packet with no human in the loop, so
every failure mode must fail closed. The shape below is the
Build 4 adaptation from the round 10 plan, and decision 11 of
`docs/decisions.md` records why it is shaped this way.

## The invocation

Run the review with `claude -p`, the prompt naming the packet
file, and the packet piped on stdin so the run needs no file
read permission of its own. The flags that matter are
`--output-format stream-json` with `--verbose`,
`--permission-mode dontAsk`, `--permission-prompts none`, and
`--json-schema` carrying the findings schema from the next
section. The `dontAsk` mode denies every call that would
otherwise prompt, which is the locked down posture a CI run
wants, and `--permission-prompts none` tells the run not to
wait on a permission host and not to retry the denied calls.
Capture the stream to a file and the exit code beside it.

```sh
claude -p "Review the packet on stdin and report findings as JSON" \
  --output-format stream-json --verbose \
  --permission-mode dontAsk --permission-prompts none \
  --json-schema findings.schema.json \
  < packet-dir/packet.md > run.jsonl
echo $? > run.exit
```

## The findings schema

The schema below is the contract the run's structured output
must match. It is deliberately small. The run reports a
verdict and a findings list, and every finding carries a
severity, a location, and the evidence paths it rests on.

```json
{
  "type": "object",
  "required": ["verdict", "findings"],
  "properties": {
    "verdict": {"enum": ["pass", "fail"]},
    "findings": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["severity", "location", "evidence"],
        "properties": {
          "severity": {"type": "string"},
          "location": {"type": "string"},
          "evidence": {"type": "array", "items": {"type": "string"}}
        }
      }
    }
  }
}
```

## The fail closed contract

Four documented limits shape the gate, and the gate treats
each one as a failure rather than as an ambiguity.

First, the exit code contract says a nonzero exit means the
run failed. The gate fails the run on any nonzero exit and
reads nothing further from the stream.

Second, a failure inside the run prints as the result on
stdout, so exit zero is not proof of a clean run. The gate
never trusts the exit code alone.

Third, a run that ends without valid structured output
carries no `structured_output` field. The gate requires the
field to be present before it reads a single finding, and a
missing field fails the run.

Fourth, the findings must match the schema above. Schema
drift between the packet and the CI output fails the gate,
because a run that cannot describe its findings in the
agreed shape has not produced a review the pipeline can
trust.

## Denial detection

The headless docs page documents the denial signal in its
section on turning off permission prompts in unattended runs.
Denials appear as `permission_denied` system messages in the
stream, and the final result message lists them in
`permission_denials`. The gate reads the final result message
of the stream and fails the run when that list is not empty.
A run whose tools were denied can otherwise look clean, so
the denial list is a load bearing input to the verdict and
never an advisory one.

## Evidence must stand in the packet

Every evidence path a finding cites must stand in the packet
manifest's file list. A finding that cites a path the packet
never gathered is a finding without evidence, and a run with
missing evidence never reads green. A pass verdict beside a
non empty findings list fails the gate too, because the two
statements contradict each other.

## What the gate checks

`scripts/check_headless.py` implements the contract above.
Give it the stream file, the packet manifest, and the exit
code, and it prints one line per problem and exits nonzero
when the run does not read green. The unit tests in
`tests/test_headless.py` are its adversarial pass, with one
fixture per failure shape from this doc.

```sh
python3 scripts/check_headless.py \
  --stream run.jsonl \
  --manifest packet-dir/manifest.json \
  --exit-code "$(cat run.exit)"
```

## Limits

The check cannot run a live host on the gate box, so its
adversarial pass runs against fixtures rather than against
real runs, and the fixtures name the exact stream shapes they
stand in for. The `permission_denied` system messages that
appear mid stream are the secondary signal. The gate reads
the final result message's `permission_denials` list as the
authoritative one, because that is the list the docs name.
Decision 4 still binds this shape. The headless run consumes
the packet as a reviewer, and nothing it judges replaces a
check the shipped scripts run.
