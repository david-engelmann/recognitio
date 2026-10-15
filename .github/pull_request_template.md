## Summary

<!-- One sentence on what this pull request does, plus the issue or
spec item it serves. -->

## Verified

<!-- The review readiness block. Review starts from evidence, so
name the exact commands, their exit codes and the head they ran on. -->

**Commands run**

```text
make check
```

**Exit codes**

<!-- One line per command, in the same order as above. -->

**Head SHA**

<!-- The full SHA of the branch head the commands ran against. -->

## Spec reference

<!-- The blueprint, decision or issue this serves. Write none when
there is no spec item behind the change. -->

## Known deviations

<!-- Every place this change departs from the spec. Write none when
it departs nowhere. -->

## Checklist

- [ ] The gate ran locally on this head and stayed green.
- [ ] Every fix in this change has a test that fails when the fix
      is reverted, and no test was weakened to make the suite pass.
- [ ] The changelog entry sits at the end of the `[Unreleased]`
      section of CHANGELOG.md.
- [ ] The docs update map in AGENTS.md was consulted and every doc
      it names for this change is updated in this pull request.
- [ ] The copy bar held on public prose in this change.
- [ ] CodeRabbit findings were fixed, or dismissed with a one line
      reason recorded in the gate report.
