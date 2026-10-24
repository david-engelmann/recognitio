# Bugbot rules for recognitio

These rules guide Cursor Bugbot reviews of pull requests in this
repo. They restate the repo's own review discipline for the
Bugbot surface. They advise and never enforce. Enforcement stays
on the shipped scripts, which the gate runs before every push.

## The rule surfaces

Bugbot reads the repo config at `.cursor/config/bugbot.yaml`
from the PR's base branch. The precedence order from highest to
lowest is the PR author's personal overrides for their own PRs,
then `.cursor/config/bugbot.yaml`, then team and organization
settings from the dashboard. The only repo YAML field the
primary docs name is `autofix.mode`, and it can only lower the
Autofix mode from the dashboard setting, never raise it. The
shipped config sets it to `disabled`, because Autofix would
repair findings with a Cloud Agent, which is model judgment in
place of script enforcement.

Effort level is a Teams dashboard setting, not a `bugbot.yaml`
control. The four levels are Low, Default, High, and Smart.
Smart does not read the PR description, labels, or BUGBOT.md
when it chooses a level.

Bugbot findings default to `neutral`. Requiring the Bugbot check
alone does not block merges on findings. Any merge gate built on
Bugbot must enable fail on unresolved issues where the
organization offers it, and must never read `neutral` as a pass.
The separate `Cursor Bugbot Autofix` check uses only `success`
or `neutral`, so requiring that check is vacuous as a gate.

Each rule below is far under the 30,000 character per rule cap,
and the combined rules are far under the 100,000 character cap.
The verbose run flag `bugbot run verbose=true` posts the table
of included rules with truncation flags for verification.

## The review rules

### B1. No invented findings

A Bugbot review never writes a finding of its own. It points at
guidance and at evidence, and judgement belongs to the review
skill downstream. A clean change with a valid exception gets no
finding.

Derives from canonical skill, The boundary, which reads "It does
not approve, reject, rank, or comment on the code. Those acts
belong to the review skill downstream, which keeps its own axes
and its own reporting rules."

### B2. The verified packet gates the review

A review is stamped only on a packet whose manifest reads
verified. A failed packet is a stop, never a smaller yes. When
verification fails, the review says what is missing in plain
words, naming the files or hunks that disagree.

Derives from canonical skill, Stamping the gate report and
Completeness discipline, which read "Never present a partial
packet as a complete one. Never let a review begin on a packet
whose verified flag is false."

### B3. Flag the instruction bearing files

A change that touches an instruction bearing file is flagged in
the review, because a change to such a file steers the next agent
that loads the tree. The name set is AGENTS.md and CLAUDE.md and
SKILL.md and GEMINI.md at any depth, the .cursorrules file name,
a Cursor rules file under a .cursor folder, and a Claude rules
file under a .claude/rules folder, with a rename flagged when
either its old name or its new name stands in the set.

Derives from canonical skill, The tier model, the T0 instruction
file flag.

### B4. Keep every rule inside the caps

Each rule stays under 30,000 characters when included in a
review, and the combined rules stay under 100,000 characters.
The verbose run flag posts the table of included rules with
truncation flags, so a rule that grew past its cap is caught by
inspection.

Derives from the primary Bugbot docs at cursor.com/docs/bugbot,
which state the per rule and combined truncation caps.

### B5. Never read neutral as a pass

Findings default to neutral, so a required Bugbot status alone
does not block merges on findings. The review treats unresolved
Bugbot comments as open work. Any merge gate built on Bugbot must
enable fail on unresolved issues where the organization offers
it, and must never read neutral as a pass.

Derives from the primary Bugbot docs at cursor.com/docs/bugbot,
which state the neutral default conclusion and the fail on
unresolved behavior.

### B6. Hard enforcement stays with the scripts

Bugbot reviews advise and never enforce. The packet gate, the
manifest recount, and the CI guards are what block a review. No
model judgement replaces a script check.

Derives from Decision 4, which binds this build like every other
build, and the primary Bugbot docs at cursor.com/docs/bugbot.
