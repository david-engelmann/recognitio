# Changelog

All notable changes to recognitio are recorded in this file.

The format follows Keep a Changelog and the project versions follow
Semantic Versioning.

## [Unreleased]

This unreleased work carries version 1.3.0.

### Added

- The recognitio skill in its first working version. The bundled
  extractor pulls the relevant changes out of a pull request, a
  commit range or a single commit from the local clone and assembles
  them into a review packet across four tiers. Triage comes first,
  then the change itself with whole enclosing function context, then
  companion call sites and test files, then history. A manifest
  records every changed file and hunk, and an independent recount
  must agree with the manifest before the packet is called verified.
- The pull request title, body and spec references in the triage
  tier, and the changed file list beside the numstat summary.
- Imports of the changed files and definitions of the changed names
  in the companion tier.
- Prior pull requests touching the same files in the history tier,
  gathered with the GitHub CLI when it is available and named as
  unavailable when it is not.
- A tier selector that chooses which companion and history tiers a
  run builds, separate from the budget mechanism.
- A findings file for re-review. Each prior finding is marked
  addressed or unaddressed by whether its anchored lines changed.
- Named placeholders for binary files and for files detected as
  generated or as lockfiles, with every placeholder listed in the
  packet header and counted in full in the manifest.
- The packet check script, which validates a packet directory
  before a review is stamped on it.
- The manifest now records the producing command, the extractor
  version and a creation time.
- A decisions file that records where the design departs from the
  research sketch and why.
- Tests for the gate scripts themselves, for pull request mode with
  a stand in GitHub CLI, and for all three budget outcomes.
- Plugin packaging. A plugin manifest and a marketplace listing
  live under `.claude-plugin/`, the plugin manifest lists the
  skill by its explicit path, and a version coherence gate keeps the version strings of
  the plugin manifest, the marketplace listing, the extractor and
  the changelog in agreement.
- An eval layer under `evals/`. A paired run over four fixture
  tasks with planted defects records what a reviewer finds from
  the packet against what the same reviewer finds from the raw
  diff, a saved trigger set scores the skill description, and a
  corpus index maps the audit incidents to the tests that cover
  them.
- Review guidance for this repo in `REVIEW.md`, covering what
  failure looks like here, the paths a reviewer may skip, a cap
  on nits, a file and line evidence rule, and the audit until
  dry stopping rule.
- A trust and limits section in the readme, with a short mirror
  in the skill text, stating what the extractor does and does
  not do and what a verified packet does not prove.
- The skills list of the official marketplace shape on the
  marketplace entry, naming the same skill path the plugin
  manifest names, and the owner email on the plugin manifest
  author and the marketplace owner.
- A fifth paired eval task with no planted defects, so a false
  lead rate is measurable, with run notes in the results file
  naming who ran each pass and when and by what method, and a
  fairer raw pass that holds the diff plus the changed file list
  with both sets of numbers reported.
- A strengthened trigger set whose near misses are genuinely
  confusable with the work the skill does, scored by a second
  independent pass with the agreement between the passes
  recorded in the trigger results.
- A review report template in REVIEW.md, with a summary first
  and findings grouped by severity and every finding carrying
  its evidence and its impact and an action item.
- A bare list of what the tool does and the named review
  workflow on the first screen of the readme.
- The round 1 branch convention finding recorded as uncovered
  in the corpus index, and the path from that index to a
  runnable corpus stated in the index and in the decisions
  file with the remaining deferral and its reason.
- A per pass notes file for the paired evals, naming who ran
  each pass, the condition it held and what it reported, so the
  record behind the results summary can be regraded.
- A held out trigger run for the skill description. The
  tightened proposal from round 1 was frozen, a fresh set of
  twenty queries was written after the freeze, and three
  description only passes scored both texts on that set. The
  proposal won and the tightened description is applied to the
  skill file in this change, with the boundary sentence that
  the skill assembles evidence only.
- A findings disposition count in the review report template
  in REVIEW.md, sorting findings into fixed and wrong and
  intentional and not worth it, so reviews that follow the
  template produce the noise accounting signal.
- A round 2 section in the corpus index, mapping every round
  2 incident to its covering test or recording it as uncovered
  in the open where the fix was prose or a record only.
- An explicit trigger in decision 3 for lifting the corpus
  index rows into a runnable suite, set at the first of a
  standalone tool decision, a round that asks for findings per
  tier per token, or the close of the audit program.
- A statement in REVIEW.md of where the findings disposition
  counts aggregate and when they are read as a signal, and the
  first populated review report written from the template at
  `docs/reviews/round4-fix-review.md` with a real four way
  disposition count of its own findings.
- A fresh eyes rerun of the paired eval by a lane that did not
  design the tasks, covering the raw and packet conditions
  over all five tasks with the clean control under both
  conditions, recorded in the per pass notes with totals that
  agree with the recorded results.
- A flag for instruction bearing files in the packet. The
  triage file list marks a changed file whose name stands in
  the instruction name set, and its manifest record carries
  the same flag as a boolean, with a rename judged from either
  of its names.
- A sixth paired eval task that replays a real merged pull
  request at fixture scale, built from pull request 9 and
  its rename finding, with the full verbatim transcripts of
  its raw and packet passes kept beside the summary in the
  task folder. The task stands as an additional task and its
  numbers join no headline total.
- Round 4 and round 6 sections in the corpus index, mapping
  each incident of those rounds to its covering tests by
  exact name and recording the record only repairs of each
  round as uncovered in the open.
- A size guard on the skill file in the skill validator, set
  at 16000 in both characters and bytes with a 20 percent
  buffer under the disclosed host cut, and a manifest
  conflict check in the version gate that fails when a
  marketplace entry specifies a component field at the top
  level of the entry or under its experimental object while
  the entry sets strict to false and a plugin manifest
  stands beside the entry.
- A review report for the round 6 fix change itself, written
  from the template in REVIEW.md at
  `docs/reviews/round6-fix-review.md` with a real four way
  disposition count of its own findings.
- A round 7 section in the corpus index, mapping each
  incident of that round to its covering tests by exact name
  and recording the record only repairs of the round as
  uncovered in the open, with the round 6 section completed
  by the two fence tests and the one review record finding
  it had omitted.
- A review report for the round 7 fix change itself, written
  from the template in REVIEW.md at
  `docs/reviews/round7-fix-review.md` with a real four way
  disposition count of its own findings.
- An eval integrity gate at `scripts/check_evals.py`, wired
  into the check beside the copy fence. The gate reads a
  checksum record at `evals/checksums.json` over every eval
  artefact file under `evals/tasks/` and over the results
  file and the per pass notes, checks the results totals
  against the per task entries the results table prints,
  rebuilds every task diff and manifest from its sources
  file and runs the shipped packet checker over each rebuilt
  packet, and fails when the corpus index cites a test name
  the suite no longer holds. A deliberate eval update
  refreshes the checksum record by running the gate script
  with its write flag and committing the record beside the
  artefacts it covers.
- A round 8 section in the corpus index, mapping each
  incident of that round to its covering tests by exact name
  and recording the record only repairs of the round as
  uncovered in the open.
- A review report for the round 8 fix change itself, written
  from the template in REVIEW.md at
  `docs/reviews/round8-fix-review.md` with a real four way
  disposition count of its own findings.
- A task-06 score re-derivation in the eval integrity gate,
  which parses the planted grading rule, verifies that each
  planted defect still stands in the head rebuilt from the
  sources file, grades each transcript fence under the rule
  and fails when the derived scores disagree with the
  recorded sentences in the results file and the per pass
  notes. Each task sources file is anchored under a digest
  record at `evals/source-anchors.json` that stands apart
  from the checksum refresh, and each corpus section is
  pinned under a coverage record at
  `evals/corpus-coverage.json` with the same standing. The
  checksum record now covers the corpus index as well, loads
  through a strict reader that refuses a repeated key, and
  spells its keys with forward slashes on every host.
  Sixteen pinning tests cover the new checks.
- A round 9 section in the corpus index, mapping each
  incident of that round to its covering tests by exact name
  and recording the record only repairs of the round as
  uncovered in the open, with the round 8 section completed
  to cover the two repairs its first writing had missed.
- A review report for the round 9 fix change itself, written
  from the template in REVIEW.md at
  `docs/reviews/round9-fix-review.md` with a real four way
  disposition count of its own findings.
- The agent conventions for the new shipping rule, with review
  changes landing on `main` by direct push of their reviewed
  commits and the coordinator checking the sign off trailers the
  CI DCO job no longer sees on the push path.
- The headless print mode CI shape. `docs/headless-review.md`
  defines the unattended review invocation with its findings
  schema and its fail closed contract, and
  `scripts/check_headless.py` gates a captured run on the exit
  code, the `permission_denials` list in the final result
  message, the presence of `structured_output`, schema
  conformance and evidence standing in the packet manifest.
  Fifteen tests form its adversarial pass.
- Build 5, the plugin reviewer persona as the main thread. The
  plugin ships an agent file at `agents/reviewer.md`, declares
  it under the `agents` key of the plugin manifest, and names
  it as the session agent under the manifest `settings` key,
  so the host runs the reviewer persona as the session's main
  thread. The persona changes the persona and not the tool
  access. A new gate script at `scripts/check_persona.py`
  pins the manifest keys and the agent frontmatter field by
  field, and forbids a tool allowlist and a permission mode as
  defense in depth, and the gate fails any persona sentence
  that is not a sentence the canonical skill text carries
  beside the pinned persona prose. The brief lives at
  `docs/reviewer-persona.md`, and decision 14 records the
  build.
- Two program record corrections from the round 15 plan. The
  Build 16 posture flips from plugin on hold to plugin build,
  because the ZCode plugin API is now fully primary
  documented, and the Build 18 condition lifts, because Trae
  Agent Skills support is now primary confirmed. Both land as
  decisions 12 and 13 under the retrospective correction
  convention.
- Build 6, dynamic workflows for review fan out. One reviewer
  reads each file group and an adversarial second pass re
  reads every finding, exploiting the `multiagent_20261001`
  default with schema validated JSON findings through
  `claude -p --json-schema`. The runbook lives at
  `workflows/review-fanout.md` beside the portable core, the
  findings schema at `workflows/findings.schema.json`, and a
  new gate script at `scripts/check_fanout.py` fails a run
  whose groups drop a file, whose merge did not dedupe, whose
  second pass left a finding without an evidenced verdict, or
  whose concurrency caps exceed the primary numbers of 16
  concurrent locally and 64 on managed runs with 1000 agents
  per run. A shipped proof run under `workflows/proof-run/`
  shows overlapping groups, a merged finding, a contested
  finding, and a planted defect the first pass missed and the
  second pass caught. Decision 15 records the build.
- A change to a plugin agent file under `agents/` is now
  flagged as a change to an instruction bearing file, the way
  decision 10 did for the output style. The gate pins the
  `agents/` directory to exactly the declared agent file.
- Build 7, the Claude Code mod with in process hooks. The
  hooks module under `hooks/` registers an `agent.spawn`
  hook that denies a review spawn unless the packet manifest
  named by `RECOGNITIO_PACKET_DIR` reads verified, with a
  `.catch` handler returning the deny shape so a hook crash
  fails closed. The brief at `docs/mod-build7.md` records
  the second layer fail open as a stated limit, and the
  repo gate pins the mod contract in `scripts/check_mod.py`.
  Decision 16 records the build.
- Build 8, the Agent Plugins 1.0.0 portable package. The package
  at `agent-plugins-package/` carries the closed schema manifest
  and the skills tree as the portable core, with the Claude Code
  native shapes riding beside it at the repo root as per platform
  extensions declared under the reverse domain namespace the spec
  section 8 defines. The gate pins the ten field manifest schema
  in `scripts/check_package.py`, so a native manifest key can
  never slip into the portable manifest and be silently ignored,
  pins the package skill byte identical to the canonical skill,
  pins the `mcp.json` omission, and pins the brief sentence that
  the package does not install natively in Claude Code on current
  evidence. The brief at `docs/agent-plugins-brief.md` records
  the section 8 mechanism per shape, the single source rule for
  the package skill, and the two governances kept distinct.
  Decision 17 records the build.
- The Codex review rules package at `docs/codex-review-brief.md`.
  It exploits OpenAI's custom code review rules surface, the
  codex-plugin-cc Stop gate with its usage loop warning, and the
  dedicated cloud environments reference. Every rule carries a
  derivation note naming the canonical skill section or gate it
  restates or the primary OpenAI citation it reports, pinned by
  the gate in `scripts/check_codex.py`, so the scoped guidance
  cannot become a rival instruction source. The brief rests the
  Security Cloud surface on the three primary citations, states
  the no product native calendar schedule negative plainly,
  carries the default branch only and completion versus coverage
  limits, names the two pauses separately, dates and scopes each
  model pin to its surface, and folds in the openai/codex-security
  CLI and SDK material, the PR review artifact layout, the
  review_model key, the Guardian auto review keys, the threat
  model draft and edit loop, and the CI example with the same
  repo guard. Decision 18 records the build.
- Build 10, the Cursor plugin. The manifest at
  `.cursor-plugin/plugin.json` follows the primary packaging
  rules with the six component set, and the skill ships as a real
  directory copy under `skills/recognitio/`, byte identical to
  the canonical skill, because the host skips a symlink that
  points outside the local plugin folder. The plugin ships no
  agents, no commands, no MCP servers, and no hooks. The Bugbot
  rules at `.cursor/BUGBOT.md` carry derivation noted rules and
  pin the effort level as a Teams dashboard setting, the neutral
  default with the fail on unresolved gate, and the rule caps.
  The repo config at `.cursor/config/bugbot.yaml` sets
  `autofix.mode` to `disabled`, and the gate rejects unknown
  fields because they fall back silently. The brief at
  `docs/cursor-plugin-brief.md` is pinned by the gate in
  `scripts/check_cursor.py`. Decision 19 records the build.
- Build 11, the CodeRabbit guidelines build. The brief at
  `docs/coderabbit-review-brief.md` exploits the Code Guidelines
  entry reading `.claude/rules/` with `paths` frontmatter,
  pairing the packet with the autonomous fix loop for the review
  fix cycle. Every guideline carries a derivation note naming the
  canonical skill section or the primary CodeRabbit citation it
  restates or the binding decision it follows, pinned by the gate
  in `scripts/check_coderabbit.py`, so the scoped guidance cannot
  become a rival instruction source. The brief records the rename
  direction as primary, with Fix comments formerly Autofix and
  Autofix formerly Autopilot and compat aliases kept. It records
  the focus toggle table as the constraint, with high trimming
  verbosity and never reading as deeper review, the focus and
  profile axes named on every sentence, and the summary fold at
  high pinned explicitly. It records the Quiet, Chill, and
  Assertive profiles with the July 2 2026 Quiet launch, the pre
  merge checks with Error mode merge blocking, the Automatic
  Approvals surface, and the approval risk limits, the October
  2026 Deep Scan and `reviews.allow_author_approval` entries, and
  the guideline file provenance now shown in review summaries,
  with `.claude/rules/` as the fourth guideline source. Decision
  20 records the build.
- `scripts/check_test_vacuity.py`, the test vacuity guard, joins
  the gate as its own step. Every test method must carry a real
  assertion and touch a fixture, which answers the joint check
  plus test softening attack, and the guard catches the crude
  joint softening (vacuous bodies), not subtle tautologies over
  fixture derived values, with the spec lane diff review staying
  the guard for that shape.
- Build 12, the Antigravity plugin alteration. The brief at
  `docs/antigravity-plugin-brief.md` records the Antigravity
  plugin format with `plugin.json`, `skills/`, `agents/`,
  `rules/`, and `hooks.json` per the primary Google docs read
  as text on 2026-10-24, and a `PreToolUse` hook carrying the
  `deny`, `force_ask`, and `auto_approve` decisions as the
  build's declared mapping for the review run tool call,
  because the primary hooks page names no `agent.spawn` event.
  The dated October 9 2026 sunset evidence names Antigravity
  as the forward path for agentic coding assistance, the
  v0.65.0 stable pin stands with the docs lag caveat trusting
  the releases page over the docs page, and the Antigravity
  native shapes ride as a second extensions namespace beside
  the portable core, never blended into it. No primary source
  names a reverse domain namespace for an Antigravity plugin,
  so the portable manifest uses `com.google.antigravity` as a
  documented placeholder. The harness contract is the
  repo-documented contract, and a missing or unparseable hook
  file is a planned degraded state that fails the gate, never
  a silent pass. The gate script at
  `scripts/check_antigravity.py` pins every dated and
  structural sentence, and the package gate now resolves every
  namespace in the extensions object and pins the package root
  tree to `plugin.json` and the `skills/` tree. Decision 22
  records the build.
- Build 13, the Copilot SDK agent build. The brief at
  `docs/copilot-sdk-brief.md` records the Copilot code review
  surface as primary. Head branch instructions are untrusted
  input, merge authority lives in base branch CODEOWNERS and
  rulesets only, an approval never fires on a red packet, and
  model pinning stays at capability level with no named review
  model. The gate at `scripts/check_copilot.py` pins every
  rule's derivation note and the three adversarial pins the
  round 26 red team proved. Decision 23 records the build.
- Build 14, the Kimi managed plugin. The brief at
  `docs/kimi-plugin-brief.md` records the managed plugin surface
  as primary. The manifest `agents` field carries auto discovery,
  the collision precedence is explicit, plugin skills are invoked
  under their qualified names, hooks run in the session project
  directory in the global scope and at the plugin root in the
  plugin scope, the four hook events are observation only,
  the limits are 32KB per `systemPrompt` field and 64KB total,
  unsupported runtime fields appear as diagnostics, and print
  mode CI runs under the reviewer persona. The gate at
  `scripts/check_kimi.py` pins every rule's derivation note and
  the six adversarial pins the round 27 red team proved, with a
  live observation test over the four hook events. Decision 24
  records the build.
- The Build 14 gate is hardened in round 28. Its negative checks
  now forbid each pinned claim in any phrasing, not only in the
  exact planted sentence, and every pinned claim now carries a
  negative check. The derivation check covers unnumbered rule
  headings and paragraphs after a derivation note, and a bare
  citation no longer passes it. The decision record pins its
  load bearing fragments, the extractor flags the Kimi plugin
  surfaces as instruction bearing, the live hook probe runs pass
  mode as well as fail mode, and the collision fixture contents
  are pinned. Decision 25 records the hardening.
- The round 29 pass hardens the Build 14 gate further against
  reworded contradictions, with a negative check for every
  pinned claim including the agents auto discovery, the built
  in override, the four hook events, the print mode stay alive,
  and the decision 4 statement, and with negation aware limits
  so a correct restatement in negative form passes. The live
  hook probe now requires the output to prove the requested
  event ran and no other, and the probe is part of the gate
  function itself. The Copilot gate is hardened in the same
  meaning based style for head branch trust and approval
  permission. The extractor flags the plugin root
  `kimi.plugin.json` manifest by basename wherever it sits.
  Build 16, the ZCode plugin build, lands with its native
  manifest at `.zcode-plugin/plugin.json`, the marketplace
  version bump rule, the register but not execute behavior,
  and the format limits. Build 15, the Qwen Code marketplace
  presence, is deferred by dated decision to round 33.
  Decisions 26 and 27 record the deferral and the build.
- The round 31 pass lands Build 17, the Devin playbook and
  coordinator build, with its derivation noted brief at
  `docs/devin-playbook-brief.md`, its gate script at
  `scripts/check_devin.py`, and decision 28. The Build 14
  and Copilot gates are hardened against replacement
  rewording and new synonyms, so an in place rewrite of a
  rule sentence and a synonym trust or approval claim now
  fail the gate. The Build 13 brief gains the October 22
  through October 26 2026 global default window with its
  explicit choice note, the October 19 2026 model policy
  API, the October 23 2026 totals by client metrics with
  the best effort and calls not prompts caveats, the
  October 23 2026 Teams legacy retirement, and the October
  13 2026 Gemini 4 Argon availability, and the November 16
  retirement coverage is named across all GitHub Copilot
  experiences with no code review claim from that entry.
  The Build 10 brief gains the Cursor Security Review bot
  separation with scope, team rules, draft skip, and the
  Teams and Enterprise plan gate, plus the Origin App
  Marketplace CodeRabbit launch path. The Build 11 brief
  gains the CLI v0.9.0 cloud task surface with signed Linux
  release verification and the Deep Scan linked repository
  limits. The Kimi brief gains the KIMI_CODE_TRUST_WORKSPACE
  note for fresh checkouts and the unversioned reference
  layout statement, and the ZCode derivation notes gain
  their retrievable page URLs. Decision 25 is narrowed by
  dated note to the phrasing families the gate tests,
  decision 26 is annotated with the 12 versus 16 conflict
  and the internal verify exit 4 scope, decision 13 is
  annotated with the UNVERIFIED Trae skill surface, and a
  round 31 note homes the corrected Graphite CLI changelog
  pin. The Codex brief gains the CLI 0.164.0 promotion,
  with the ten preset slots scoped as TUI slots only and no
  skill format claim for presets. The fan-out runbook gains
  the limitation note that it carries no flipped task eval
  and no repeated run comparison.
- The round 32 pass rewrites decision 13 to a single
  suspended status and defers Build 18 by dated decision,
  because the round 32 primary check found no Trae skill
  or plugin surface. The round 15 entry line about the
  Build 18 condition lifting on primary confirmed Trae
  support is superseded by the round 31 annotation and the
  round 32 deferral, and the old entry stands as history.
  The Devin gate gains semantic negatives for the resolved
  count, the bypass surface, and the SARIF export shape.
  The Copilot and Kimi gates gain negatives for fresh
  trust, approval, precedence, and bare name phrasings.
  The README prints pinned install forms in a later
  Pinned forms section for the older routes, and the docs gain the model policy API
  naming, the POST 403 derivation locator, the November 16
  re-check diary note, and the layout map completions.
- The round 33 pass lands Build 15, the Qwen Code
  marketplace presence, with its derivation noted brief
  at `docs/qwen-code-brief.md` and its gate script at
  `scripts/check_qwen.py`. The figure resolution is a
  basis and scope table with no single figure as the
  Qwen figure, the exit table scope keeps wrapper exits
  0, 1, and 3 separate from internal verify exit 4, the
  extension routes tested are the Qoder conversion and
  the Agent Plugins v1 install with the scoped npm route
  left untested, runtime invocation stays UNVERIFIED,
  the README gains a Qwen install section with pinned
  forms in the same section, and the layout map gains a
  bullet naming the brief and the gate script. No Qwen
  listing file ships in this round and the version stays
  1.3.0.
- The round 34 pass consolidates the rounds 31 through
  33 builds with no new build. It closes the round 34
  audit findings, adds the rounds 15 through 24 sections
  to the eval corpus index, and carries every round 33
  residual in its current wording, with Qwen runtime
  invocation UNVERIFIED, the scoped npm route UNTESTED,
  release asset shapes beyond the introduction page
  UNVERIFIED, Qwen docs snippet provenance UNVERIFIED
  and unused, Open Code Review v1.13.3 with no claim
  made, the round 28 silence detail as program record
  only, and the round 32 external scoped shape guard
  carried forward. The Copilot October 22 through
  October 26 window re-read and the November 16
  retirements recheck stay owed after their dates pass.
- The round 36 pass hardens the landed build gates
  against the round 36 audit findings with no new build.
  The Copilot trust and approval negatives now read the
  whole brief instead of the rules section alone. The
  Kimi gate catches the per field and total figure swap
  and a bare name stated as the subject of an invocation.
  The Cursor gate rejects a repository cap figure stated
  without the R35-C-01 conflict note beside it, a
  bugbot.yaml effort pin, and a merge blocking neutral
  conclusion. The CodeRabbit brief gains the Deep Scan
  linked source platform limit and the default branch pin
  beside the linked context sentence, and its gate rejects
  linked source promised on an excluded platform and any
  linked repository figure other than 20. The ZCode gate
  rejects an execution claim for the registered fields
  and a description cap other than 1024 characters. The Qwen
  figure family gains sentence scope, and the Devin
  membership branch catches membership stated through a
  pure modifier chain, closing the two structural escapes
  the round 36 metamorphic generation lane proved. The
  Devin brief restates its SkillsBench claim under the
  version 4 citation rule, the Antigravity brief states
  the Gemini Code Assist on GitHub split status, and the
  README install guidance states that copies do not
  inherit upstream fixes. The accepted round 34 single
  synonym residual stands unchanged. The three review
  gate on this pass then restated each new branch in the
  forms just outside its first shape, and a repair commit
  widened the branches to read scope binding, sentence
  pairs, clause level guards, and figure binding in
  place of the first narrow forms, with the false
  positives the widening first carried guarded out.
- A visual pass over the README. The file now
  opens with a badge row, a recorded demo of a real
  extraction run, the paired eval result, and a
  packet excerpt set against the raw diff for the
  same commit, and a flow diagram and a platform
  adaptation table stand further down. The version
  gate now reads the README version badge as one of
  the surfaces that must agree.
- The README demo is now an agent session. A
  real model reviews the range from 365da81e to
  ecdda4c8 from the packet the extractor built
  for it in the same run. The loop opens on the
  raw diff of the range, all 3,233 lines of it,
  before the packet distills it.
- The round 37 pass hardens the landed build gates
  against the round 37 audit findings with no new build.
  The Copilot trust and approval negatives now read
  triples of neighbouring sentences, and both scans
  honour a negative quantifier standing after the verb.
  The Kimi swap binding reads the whole sentence with no
  gap limit, and its bare name verb branches read the
  whole segment. The Cursor cap and effort branches read
  the whole sentence, with a unit word rebinding a cap
  figure to a different quantity, and the neutral branch
  reads sentence pairs. The CodeRabbit linked branches
  read sentence pairs and bind at unit scope, and a
  negation standing before an offer in the same claim
  stretch guards the pair. The ZCode execution reading
  judges the sentence with its guarded clauses removed,
  and its description figures are read from the whole
  sentence against their own clause. The Qwen figure
  family reads windows of three sentences, and a window
  is exempt only when every sentence in it that carries
  a bound figure is guarded in the figure own clause. The Devin modifier chain now reads any word
  that starts no new claim unit, and its negation guard
  reads the whole claim stretch. The Qwen brief records
  the round 37 full bundle conversion attempt with its
  three named differences, the skill line rewrite, the
  dropped author and license fields, and the mirror
  trailing newline, and the gate pins the record. The
  pinned figure rules are stated as other than in place
  of above wherever the gates test inequality. The
  accepted round 34 single synonym residual stands
  unchanged. The three review gate on this pass then
  filed fresh plants against every widened branch, and a
  repair pass widened the Copilot authority and
  CodeRabbit linked readings to triples and the Qwen
  figure windows to four sentences, scoped each negation
  and guard phrase to the claim it guards, bound the
  Qwen figures by their own clause, judged the ZCode
  figures in their own clause, bound the Cursor figures
  by their own count noun, and bound the Kimi figures
  by their own scope word. A confirmation pass over the repair
  then widened the Qwen figure windows to five sentences
  and closed the remaining fresh shapes of the same
  seams.
- A filed confirmation repair closes the thirteen
  findings and two unnumbered verified shapes of the
  confirmation red team report as filed, beyond the
  summary the fix lane first acted on. A Copilot subject
  sentence now guards only when it also states the
  claim predicate. The Kimi clause boundary and the
  Cursor unit split and guard tail no longer require
  the comma the joint may omit. The CodeRabbit windows
  run to four sentences and the clause resets read the
  claim noun subject beside the pronoun forms. The
  ZCode execution reading judges the text on both
  sides of a guard phrase, the inheritance binding
  reads the deictic reference beside the inheritance
  verbs, and the separated figure filler allowance
  stands at a measured twelve plain words. The Qwen
  figure guard clause now ends at an as joint as well
  as at a comma. The Devin chain tail reads its of
  phrase on a wider reach and its guard resets read
  the noun subject beside the pronoun forms.
- The README demo now ships in two renderings of the one
  recorded run. The chat rendering leads the page and the raw
  terminal rendering closes the See it on a real change
  section, and the single rendering they replace is gone.
- The round 38 pass consolidates the landed build gates
  with no new build. Every brief reading that stopped at
  a fixed neighbouring window now reads at claim scope,
  the Copilot trust and approval readings and the
  CodeRabbit linked readings over every neighbouring
  window inside a headed block, the Cursor neutral and
  cap readings joining deictic continuations inside the
  same headed block, and the Qwen figure windows at
  claim scope over consecutive prose paragraph groups. The Copilot
  authority branches judge each occurrence in its own
  sentence, the Kimi bare name segment breaks at the yet
  joint, the ZCode execution reading keeps the text
  between guard phrases under judgement, and the Devin
  chain tail reads the whole remainder of its sentence
  with article led subject restatements resetting its
  claim stretch. The copy fence now covers the
  Antigravity and ZCode plugin manifests. The Qwen brief
  scopes its side shape sentence to the installs it
  describes and restates the installer mirror once as a
  mirror of the input manifest, decision 26 gains a
  dated correcting note, the README adaptations table
  gains the Antigravity row, the Cursor brief carries
  the round 38 attempt note with its load behaviour
  still UNVERIFIED, and the eval corpus index catches
  up through round 34. The round also records the
  round 36 E1 fixture correction, that the four
  fixtures P008 and P009 and P012 and P013 have exited
  1 since the round 36 landing rather than standing at
  their recorded exit 0, with the correction note
  appended to the fixtures record. The accepted round
  34 single synonym residual stands unchanged.
- The round 39 pass closes the record gaps the pre close
  audits filed with no new build. The eval corpus index
  catches up through round 37 with the round 35 section
  standing in its research round form, this file states
  the round 38 gate scope in its final headed block and
  claim scope form, the AGENTS chronicle gains its round
  38 entry, and two predecessor framings in the Kimi
  limits docstring and the round 37 bullet above stand
  restated in the form the gates run. The packet stamp
  now reads the manifest tier receipt against the packet
  bodies and the manifest file records against the
  change tier entries, so a thin packet cannot wear a
  full tier receipt and a dropped changed file entry
  fails the stamp, and the gate suite now pins the
  recorded executable modes of the gate scripts and the
  extractor and the recorded mode of the skill symlink.
  The heading and barrier and sentence scope seams the
  round 39 red team filed stand frozen as closing
  residuals with their reasons in the round 39 fix
  report, and the accepted round 34 single synonym
  residual stands unchanged.
- A principles page at docs/principles.md states what a
  review packet owes its reader as claims, each one beside
  the failure in this project record that produced it, and
  the README links it from the Going deeper section.

- The demo assets rebuilt in visual round 3. The hero
  recording is rebuilt from the same recorded session
  through the builder now shipped in the repo at
  docs/images/build_demo.py with its capture record
  beside it, opening on a loaded frame instead of a
  black canvas, holding its verdict clear of the
  header bar, and running 14.48 seconds at 694336
  bytes. The terminal recording leaves the page as a
  loop and returns as three stills from the same run
  beside a hero poster still and its detail crop, and
  a new asset gate pins the hero dimensions and byte
  budget, the frame zero content, the verdict rest
  frame, the stills and every README image reference.

- The packet face rebuilt in visual round 4. The header
  fields stand in their own blocks with the verified
  marker pointing at the closing recount, a contents
  block generated from the manifest opens the packet,
  and the closing section is now the verification
  recount, printing the manifest counts and the recount
  agreement with the budget figures as facts and ending
  on the limit sentence. The header lists split files
  shown in full from files not shown in full, cap notes
  stand grouped under one Cap notes block in one
  wording, and a history cap prints once in the packet.
  The describing surfaces name the packet as four tiers
  and a closing receipt, the output style marks its
  Re-review heading as standing only on re-review runs
  and gains the fixed P1 and P2 and P3 severity
  vocabulary for the review side, and the README worked
  example shows the real added lines of its function
  with its elisions marked and counted.

- The demo assets and the README diagram rebuilt in
  visual round 6. Every demo asset now carries a two
  pixel border ring inside its canvas edge in a grey
  that measures 5.24 to 1 against the GitHub dark
  canvas and 3.61 to 1 against white, drawn by the
  demo builder as chrome around the untouched session
  pixels. The detail crop is recropped tight on the
  card header at 360 pixels wide, magnifying the
  frame 2.21 times where the old crop managed 1.11,
  with its edges on blank bands and its caption
  standing under it. The alt texts describe the
  frames they name and the badge alts name the
  passing state and MIT. The How it works diagram
  draws the recount as a decision diamond with
  rounded start and outcome shapes and no theme pin.
  The Antigravity row of the adaptations table is
  halved, and the asset gate pins the ring, the crop
  geometry and the still hashes.

- The docs set given its structural layer in visual round 7.
  A documentation index now stands at `docs/README.md`,
  grouping all fifteen documents by type with a relative
  link, a short description and a status word for each one.
  Every document opens with a back link to the index and
  every brief opens with a summary above its existing text
  and closes with a navigation block. The principles page
  is rewrapped with no word changed and three paragraph
  breaks where its subject changes. The headless runbook
  states the session limit in its limits section. Inside a
  provider session the packet is never rendered for the
  person watching the session, and that sentence now stands
  in the runbook where a reader of its limits meets it.

- The brand assets in visual round 8. A wordmark in a
  light and a dark variant and an icon and a social
  preview now stand under `docs/brand/` beside a palette
  record and a builder that outlines their lettering
  from the Liberation Sans fonts into paths and renders
  their PNG exports through CairoSVG, so no shipped SVG
  holds live text and no viewer font can move the brand
  name. The palette freezes one ground pair and one ink
  pair and the coral accent, with the verified green
  recorded as reserved and banned from every brand
  asset. The Claude plugin manifest names the 512 pixel
  icon and the Cursor plugin manifest and marketplace
  entry name the icon master as their logo, while the
  surfaces whose schemas document no image field gain
  none. The README leads with a centred picture element
  at a rendered width of 300 holding the two wordmark
  variants with the light SVG as its fallback, and a
  brand gate joins the check target with asset pins in
  the gate script suite.

- The README cold eyes fixes in visual round 9. The
  Install section opens with a heads up stating the
  requirements and the two session effects of the plugin
  route before any route command, and the pin block now
  names the commands and files a route will run. The
  Qwen subsection names the maintainer and carries no
  round language. The tier model names the five
  languages the definition patterns cover, the demo
  lead in carries the receipt of its recorded run, the
  pericope is glossed where the Usage section first
  uses it, the eval paragraph states the tied result
  beside the constructed one, the hosted diff claim in
  the Why section carries the research attribution,
  and the worked example states the true relationship
  of its two function names.

- The README rebuilt as a lean storefront after the
  visual program. The wordmark picture stands as the
  one hero lockup with no heading repeating it, the
  chat capture and its poster and terminal stills and
  detail crop retire from the page and the tree, and
  a recording of a live Cursor agent session over the
  same change stands as the one demo image, with one
  frame of it linked as a still in the lead in and
  its capture record shipped beside the assets, and
  the page weight ceiling rises once on the record
  to hold the recording. The worked
  example keeps the raw hunk and one trimmed packet
  excerpt, the Install section gives every route its
  own subheading with pinning explained once, and the
  Usage commands wrap so every command fits its block.
  The tier model and the trust and limits text move
  behind links to the skill and the principles page in
  a closing Going deeper section, and the completeness
  guarantee moves with them under its skill name of
  the completeness discipline. Every claim the page
  carried stands in
  compressed form, and the storefront tests re-pin
  the first screen order, the picture form, the image
  references and the page weight.
- The Claude marketplace listing now offers the Build 7
  mod as its own entry beside the skill plugin. The
  recognitio-mod entry is sourced from the new plugin
  folder at `plugins/recognitio-mod/`, which carries its
  own manifest, its own README and byte identical copies
  of the hooks module and its host side tests, so a setup
  can install the spawn gate without the skill bundle.
  The discovery gate pins the entry set by name and the
  mod entry by its source in place of the earlier single
  entry count, with each entry carrying the tags of its
  own manifest, the mod gate pins the copies to the
  originals, and the submissions gate pins the mod entry
  beside the plugin entry. The README install section gains the shell form
  of the marketplace add command, a table with one line
  per plugin the listing offers, a layout subsection and
  the hooks disclosure the Claude submission pack had
  recorded as open.
- The regeneration gate at `scripts/check_regeneration.py`
  and the proof run sources file at
  `workflows/proof-run/sources.json`, which together rerun
  every gated provenance claim in the tree on every check.
- The phone hero composition in place of the shipped
  phone crop. The file at
  docs/images/recognitio-cursor-agent-verified-crop.png
  now stacks two moments from the same recorded session
  as two outlined panels, the merge base line and the
  verified sentence from the frame at 230 seconds above
  and the Verdict heading and the opening of the verdict
  paragraph from the frame at 433.5 seconds below, so a
  phone reader sees the hash whole and the verified
  clause whole and the verdict whole at a legible scale.
  The shared hero alt names the verified packet as well
  as the verdict, a disclosure sentence stands under
  the hero picture element on the README, and the
  capture record names the file as a composition beside
  its asset list and states its figures. The demo asset
  gate re-pins the crop geometry and hash and the page
  weight exact total, and the hero picture test pins
  the shared alt.
- A symlink census pin in the test suite. The test
  derives every entry at symlink mode through git from
  two listings, the committed tree at HEAD and the index
  in the form its entries stand staged, and holds each
  census to exactly one entry, .claude/skills/recognitio
  with its recorded target
  ../../.agents/skills/recognitio, so a symlink planted
  anywhere else and a retarget of the legitimate link
  both fail in the discover step the gate already runs
  first once the plant or the retarget stands committed
  or staged. A link standing in the working tree alone,
  neither staged nor committed, stands outside the pin.
### Fixed

- The Build 8 brief now records the Agent Skills donation
  transfer as primary on both halves, read from the Linux
  Foundation release and Anthropic's own post in round 20. The
  older secondary corroborated wording was stale by timing, and
  the gate pins the corrected sentence.

- The fan out validator now fails a second pass verdict
  that names a finding outside the merged set. A phantom
  verdict for a nonexistent finding previously read green.

- Paths that git quotes no longer drop out of the packet. Path data
  moves through NUL delimited output, and every git invocation runs
  with its output format pinned, so ambient configuration in the
  clone or in a global config file cannot reshape the diff.
- Binary files and non UTF-8 content no longer crash the extractor.
- A text file the tree marks binary through its attributes file is
  counted and shown as text, and named in the receipt.
- Pull request mode no longer falls back to a same named local
  branch. It fails loudly when the refs are not in the clone.
- Shallow clones are refused with a clear message.
- The completeness recount covers added and deleted lines and old
  paths as well as files, statuses and hunks.
- The token budget accounts for the whole packet, and the receipt
  reports tokens per tier, files per tier and what was cut.
- A failed run no longer leaves a previous verified packet standing
  in the output directory.
- A root commit no longer records the empty tree as its merge base.
- Call sites in files whose path contains a colon are found again.
- Packet text preserves the bytes of the change, CRLF endings
  included.
- An unrelated since ref now produces an explicitly empty and
  scoped re-review section instead of a confident one, and a since
  ref on its own is no longer accepted as a mode.
- The DCO job exempts dependabot by actor and requires the exact
  sign-off identity on human commits, and the copy gate now scans
  every public prose surface in the repo.
- A second hardening round from review. The DCO job now reads the
  trailer block of a commit message instead of the whole message,
  the copy gate stops exempting punctuation that trails a link, and
  the packet check rejects an empty packet file and a manifest that
  is not a JSON object. The extractor pins the grep column and the
  inter hunk context settings, scrubs git location variables from
  the environment of its child processes and gives every child
  process a timeout. Deleted files are read through their entry
  path, so a deleted binary or generated file keeps its placeholder
  and its receipt line. Findings accounting keys its ranges by the
  path a finding was anchored under, ignores pure insertions, and
  the re-review section gates on a shared merge base, so a rebased
  head is re-reviewed instead of skipped.
- Replace refs can no longer swap the content under review. Every
  git invocation refuses replace objects, the child environment
  pins the same refusal, and the packet check reads the head under
  the same discipline.
- The line recount parses hunks structurally, so a content line
  whose text begins with two plus signs or two minus signs counts
  as content instead of being skipped as a diff header. Ordinary
  changes carrying SQL comments or TOML delimiters verify again.
- Attribute marked files are measured from numstat read with the
  text flag and cross checked against the diff body like every
  other text file. Their counts can no longer rest on one counter.
- Per file re-measurement diffs under literal pathspecs and under
  both names of a rename. A renamed attribute marked file is
  measured as its real delta, and a file named with glob
  characters shows its own diff rather than a neighbour file's.
- The range diff and the diff stat fallback in the re-review
  section carry the same pins as every other diff, and the range
  diff reads attributes from the empty tree, so a text conversion
  driver in the reviewed tree cannot rewrite the re-review. The
  range diff also pairs commits at the maximum creation factor,
  because a small commit pairs with nothing at the default factor
  and its inner diff would vanish from the re-review.
- The companion searches read attribute marked files as text. A
  tree that marks its sources binary can no longer hide its own
  call sites and leave the packet reporting that none exist.
- GitHub CLI failures of every shape now end in the failure
  receipt and the exit code the contract promises. A missing CLI,
  an unparseable answer and a wrongly shaped one no longer escape
  as tracebacks.
- A run rejected while its arguments are checked clears the output
  directory and leaves the failure receipt like any other failed
  run, so the standing promise about stale packets holds without
  qualification.
- A generated file marker withholds a diff only when the marker
  already stood at the base revision. A marker that arrives in
  the change is flagged in the packet header and the change is
  shown in full.
- The pull request body, the numstat block and the commit list
  are fenced with a fence longer than any run of backticks inside
  them. Reviewed text can no longer break out of its fence and
  forge a packet section.
- The manifest records the section headings it emitted and the
  packet check verifies those sections are present and filled,
  so a thin packet cannot wear a full packet's manifest. The
  headings are counted outside the packet's fences on both
  sides, so quoted text from the change under review cannot
  stand in for a section, and a manifest that records no
  sections fails the check outright.
- Findings accounting reads the head tree once instead of once
  per finding, is capped at one hundred findings with the cap
  stated in the section, and names an empty findings file in the
  re-review section instead of letting it vanish.
- The exclusion receipt holds one entry per file. An attribute
  marked lockfile is receipted once, as the lockfile it is shown
  as, and never also as a file shown as text.
- The prior pull request lookup states the window it covers in
  the packet and in the docs, and the receipt prose defines what
  the files per tier counts count.
- The copy gate scans the issue template config file and the
  comment prose of the workflow, the dependabot config, the
  Makefile and the gitignore file, so the coverage the gate
  claims is the coverage it has.
- The budget decision measures each candidate packet by
  assembling it, the same fixed point the shipped packet is
  measured at. A fixed allowance for the completeness section
  undercounted it whenever the section grew, and packets the
  budget accepted could land over the budget.
- The pipeline is split into named stage functions, and the
  packet write fails in the same clean voice as every other run
  failure instead of escaping as a traceback.
- A filename carrying a newline can no longer forge packet
  sections or corrupt its own line counts. The numstat parser
  reads a path across newlines to the true end of its record,
  and the packet escapes control characters wherever it names
  a file, while the manifest keeps the true path as data.
- Findings anchored to paths that never existed at the previous
  reviewed revision or at the head are no longer counted as
  addressed. They read unaddressed with the reason stated, so a
  mistyped or crafted path cannot inflate the addressed summary.
- A file that changed from binary content to text is receipted
  by that transition instead of as marked binary by repository
  attributes, and raw NUL bytes from the old binary side are
  named in the packet rather than carried into its text.
- Three generated packet sentences that carried banned marks are
  plain sentences now, and the suite scans generated packet
  prose for the marks over a binary change and over a re-review.
- The skill validator now enforces the frontmatter name
  character rules of the specification, so a rename or a second
  skill cannot break them without the gate noticing.
- Cap notes in the companion and history tiers now print escaped
  paths like every other packet surface. A crafted filename
  combined with a capped companion surface could previously
  print a forged budget and completeness heading inside a
  verified packet, and the manifest recorded the forged heading
  and the packet check stamped the pair verified.
- The companion search parser now reads its NUL delimited
  records in order instead of splitting the output on lines. A
  newline inside a filename previously truncated its hit paths,
  and a verified packet printed one file lines as call site
  context for another and reported that no test files mention
  the changed code when a crafted test file did.
- Duplicate findings entries are removed before the findings
  cap is applied, and the accounting section states how many
  were removed. Repeated copies previously counted as separate
  findings and could crowd a distinct finding past the cap.
- Companion gathering runs one bulk search over the tree for
  every term it needs instead of one whole tree search per
  changed function and per changed file stem, so its cost no
  longer grows with the product of the change size and the tree
  size, and its output is unchanged.
- The version gate now reports wrong typed but valid JSON as
  named problems in its own voice instead of dying with a
  traceback, requires a non-empty plugins list in the
  marketplace listing, accepts only a strict version shape
  with no leading zero in any component, and scopes its
  changelog search to the unreleased section so a carries
  phrase inside an old release note cannot hijack the compared
  version.
- The copy gate discovers its prose surfaces by rule instead of
  holding a list kept by hand. Every authored Markdown file in
  the tree outside the generated eval packets, the description
  fields of the plugin manifests, the issue templates and the
  config comment spans stand inside the fence by construction,
  and a fence completeness test walks the tree and fails when
  an authored prose file exists that the scanner does not
  cover.
- Three answers to review of the round 2 change itself. A
  companion search that fails now ends the run with a failure
  receipt instead of reporting that nothing was found. A
  malformed version declaration in the unreleased section of
  this changelog now governs instead of falling back to a
  released heading. The copy discovery skips dependency
  directories and symlinks that leave the tree, and a missing
  plugin manifest is reported instead of passing unscanned.
- The test files section of the packet now dedupes its hits by
  file and line before the matches cap applies, and the cap
  note counts distinct lines. One line that matched the module
  stem and two function names previously printed three times
  and crowded distinct lines out of the section, and the saved
  eval packets for tasks 01 and 02 and 05 carried the same
  duplication and are regenerated in this change.
- The bulk companion matcher now holds every term to the word
  boundary rule at both ends, whatever characters the term
  begins or ends with. Terms beginning with a dot or ending
  with a hyphen and terms carrying non ASCII letters previously
  gained hits in the bulk search that the per term grep
  rejects, and a differential test over those terms now pins
  the two searches to the same hits.
- The version gate shape now admits ASCII digits only. A
  version written with a Unicode decimal digit previously
  passed the shape and agreed across every surface.
- The YAML half of the copy fence now discovers its files by
  the same location and suffix rule as the Markdown half, with
  the comment span class kept for files whose values are code,
  and the completeness walk and the discovery share one
  exclusion predicate in the gate code so the two cannot
  encode opposite rules for the same locations again. The
  discovery exclusions are the rule that governs, because a
  local tree holding a dependency directory or a virtual
  environment is a normal contributor state and those files
  are not authored prose.
- The eval runner note now describes the current method in
  full, three passes in a fixed order with the fair raw
  condition and the clean control, where it previously still
  described the two pass method round 2 replaced.
- Four answers to review of the round 3 change itself. The
  runner note now carries a gate test that pins the three pass
  method and the clean control, and the corpus index records
  the finding as covered by it. The held out trigger set and
  its per pass verdicts now stand in the trigger results file
  in full, and the proposal section is dated so a reader can
  tell which description shipped. The test files dedupe keeps
  its hits in a set per file, so a test file with many matching
  lines no longer pays a growing list scan for each new hit.
- A paired rename now contributes the old stem of the renamed
  module to the companion search beside the new stem. A test
  file that mentions the module only under its old name, for
  example through a dynamic import of that name, is found and
  named, and the test files section no longer prints a false
  absence over it.
- The copy fence now treats YAML structure as the syntax its
  docstring always said it was. The scalar values inside a
  flow mapping are scanned as prose while its braces and key
  marks stay exempt, and repeated list markers are stripped
  before the key test, so a nested sequence of mappings is
  read as structure, while plain prose values are judged in
  full as before.
- A findings entry written with a leading ./ is accounted
  under the plain spelling of its path. The same finding
  written both ways now counts once with one verdict instead
  of standing as two findings with contradictory verdicts.
- Three answers to review of the round 4 change itself. The
  old stem search now runs only for a renamed entry and not
  for a copied one, whose old module still exists under its
  own name. The copy fence now yields the scalar values
  inside a flow mapping for its scan, so a quoted prose value
  carrying a colon inside flow braces is judged while the
  braces and key marks stay exempt. The finding in the first
  populated review report now names the line range of its
  evidence, as the evidence rule in REVIEW.md requires.
- A copied entry in a re-review interval no longer writes its
  old side ranges under its source path. Those ranges describe
  the delta of the copy and not an edit to the source, and
  writing them overwrote the ranges of the source file its
  own modification and flipped both verdicts on a modify and
  copy shape inside a verified packet.
- Findings path normalisation now covers the whole path. A
  dot segment in the middle of a path, a doubled separator, a
  backslash used as a separator, stray space before the
  anchor colon, and a path written in decomposed Unicode
  form are each accounted under the one plain composed
  spelling of the file they name, while case is never folded.
- The marketplace entry now sets strict to true, so the
  plugin loads through the marketplace route. Both manifests
  specify the skill, and under the strict false entry the
  host refused to load the plugin for conflicting manifests
  while the install command still reported success.
- The YAML half of the copy fence now reads its lines
  structurally. Key recognition accepts any scalar key a YAML
  line can carry, a scalar that spans lines keeps its state
  so a key shaped continuation line is judged as prose in
  full, and a flow collection is read wherever it stands,
  after an anchor or a tag or inside a flow sequence as much
  as in the positions earlier rounds covered, while prose
  values in every one of those shapes still flag.
- The manifest conflict check in the version gate now
  follows the host on a missing strict key. An entry that
  omits the key loads as if strict were true, so the check
  fails a components pair only when the entry sets strict
  to false, and its scan reads the experimental object of
  the entry for the whole conflict field set, so a themes
  declaration in that home no longer passes a pair the host
  refuses.
- Changed instruction files are flagged on two further
  surfaces hosts load. A path specific Copilot instructions
  file under the instructions folder of .github and a
  Claude rules file under .claude/rules now carry the
  instruction file flag in the triage list and in the
  manifest.
- The skill file size guard now counts bytes beside
  characters and fails on whichever measure crosses the
  limit first, so a multibyte skill file cannot pass under
  the character count while standing past a byte counting
  host cut.
- A re-review finding now reads addressed only when the
  content of its anchored lines changed. A rename that
  flips the line endings of a file no longer marks the
  findings on its unchanged lines addressed, because the
  ranges behind the verdict are filtered by a comparison
  of the old and new content with line endings normalised
  away.
- The stateful YAML reader in the copy gate now stands as
  named helpers under the recorded function length ceiling,
  with an AST test pinning that ceiling for the file and no
  change in what the fence flags.
- The eval artefacts stood outside every gate, so a quiet
  edit to a transcript fence or a planted grading rule or a
  recorded results cell left the gate green while the
  summaries kept asking a reader to trust those files. The
  eval integrity gate now names the first artefact whose
  bytes moved off its checksum record and catches a single
  results cell edit through the totals check even where a
  checksum refresh would hide it.
- The corpus index discipline stood as a manual check, so
  renaming a cited test orphaned its corpus rows in silence
  while the suite count gave no signal. The eval gate now
  extracts the test names the index cites and fails with
  the missing names listed.
- Fixture teardown in the test suite could fail on Python
  3.10 when a file appeared inside a fixture repository
  while its temporary directory was being removed, so a
  run whose assertions all passed still errored in
  cleanup. Both test modules now remove fixture trees
  through a temporary directory subclass that retries the
  removal a bounded number of times and raises when the
  tree still stands after the bound, and pinning tests
  cover both the retry and the raise.
- The eval gate set aside any manifest entry key that no
  saved entry of a task carried, so deleting a key from
  every entry of a saved manifest passed the rebuild
  comparison once the checksum record was refreshed. The
  exemption now names the one legacy key it exists for,
  and a test deletes a key from every entry to pin the
  narrower rule.
- The totals check guarded sums and headlines only, so a
  moved per task score distribution and an upgraded task-06
  transcript each passed the gate after the documented
  checksum refresh. The gate now re-derives the task-06 raw
  and packet scores from its transcript fences, its planted
  grading rule and its rebuilt artefacts, and fails when the
  derived scores disagree with the recorded summaries. A
  moved distribution over tasks 01 to 05 stands as a
  deliberate residual in decision 8 of the decisions file,
  because those passes survive only as curated notes.
- The rebuild check anchored each task to its own sources
  file, so tampering the sources and regenerating the
  artefacts from them passed the gate after a checksum
  refresh. The digest of each task sources file now stands
  in the source anchor record apart from the refreshable
  checksum record, the checksum refresh refuses to run while
  an anchor is stale, and the task-06 check verifies that
  each planted defect still stands in the rebuilt head.
- A duplicate key in the checksum record silently overrode
  the pin, because a plain JSON load keeps the last value of
  a repeated key with no refresh step at all. Every record
  the gate trusts now loads through a strict reader that
  refuses a repeated key in any object.
- The checksum record keys were built from the host path
  spelling, so the gate failed on a pristine Windows tree
  and the refresh path would have rewritten the record in
  the local spelling. Record keys now use the forward slash
  spelling on every host.
- The corpus check named only cited test names the suite
  lacks and the corpus index itself stood outside the
  checksum record, so a dropped row or a quietly dropped
  citation passed the gate. The checksum record now covers
  the corpus index and a per section coverage record fails a
  dropped row or citation even after a checksum refresh.
- The round 8 corpus section stopped two repairs short of the
  end of its own landing, leaving the fixture teardown repair
  and the narrowed manifest key exemption with no row. Both
  repairs are now mapped to their tests in that section.
- The user facing tiers help text carried a semicolon no
  gate reached. The string is rewritten with no banned marks
  and a test scans the help output of the shipped scripts.
- The canonical skill moved to `.agents/skills/recognitio/`
  with a symlink into `.claude/skills/` for the home platform.
  The skill validator now checks both spellings with the copy
  direction pinned canonical to home, the copy fence scans the
  canonical skill prose, the plugin and marketplace manifests
  name the new skill path, and the install routes in the readme
  name the canonical source. Two spellings of one skill can no
  longer drift apart unnoticed.
- The three spellings of the skill description are pinned in
  the gate tests. A copy bar clean rewrite of the frontmatter
  description or of either manifest blurb now fails the gate,
  so the trigger results winner discipline cannot be broken
  under a green gate.
- The packaging manifests now load through a strict JSON reader
  that refuses a repeated key. A duplicate version key in the
  plugin manifest or the marketplace listing now fails the
  version gate instead of silently resolving to the last value.
- The marketplace listing is pinned to its single plugin entry.
  A second entry naming the same skill under another name now
  fails the gate.
- A wrong typed strict key on a marketplace entry is now a
  named problem. The string "false" no longer reads as strict
  true in silence.
- Four new gate messages in the eval checker that joined
  clauses with a colon now follow the file's colon free
  convention. The duplicated git config entry, the bare
  contraction form in the denial pattern, the double blank line
  in the skill text and the duplicated test helper are cleaned
  up beside them.
- Decision 3 carries an amended first event. The standalone
  tool the old event named can never be built under the
  program's ruling, so the event is now a provider adaptation
  build whose brief needs the corpus rows as runnable skill
  tasks for its evidence.
- The corpus index now covers rounds 10, 11 and 12 with their
  incidents and regression tests, and the eval gate checks that
  the scope sentence at the head of the index names the highest
  round section it carries, so a complete index reads apart from
  one abandoned mid program.
- The plugin ships the review packet as an output style with
  force for plugin semantics, declared in both the plugin
  manifest and the marketplace entry. The style is a second
  spelling of the packet with no instruction beyond the
  canonical skill text, and the gate pins its guarantee
  sentences, its heading list and its force field against drift.
  The README discloses the session global reach and the
  subagent boundary.
- A change to the packet output style is flagged as a change to
  an instruction file in triage and in the manifest, and the
  copy fence now scans the plugin directory by rule.
- The packet output style now ships at `output-styles/packet.md`
  at the plugin root, which is where the vendor manifest
  reference resolves the declared `./output-styles/packet.md`
  path. The file previously sat under `.claude-plugin/`, which
  no declaration names, so the style never loaded on the host
  while the gate stayed green on a hardcoded prefixed path. The
  existence pin now resolves the declared path against the
  plugin root the way the host does, and the extractor flags
  the new location as an instruction file.
- The derivation section of the output style is now pinned word
  for word. The sentence check used to skip the whole section,
  so a novel instruction or a non http external reference
  planted there passed the gate green. Any added or altered
  derivation sentence fails the pin, and a subheading planted
  inside the section cannot end the pinned region early.
- The style sentence check now matches whole sentences instead
  of substrings. An imperative inversion of a pinned
  prohibition previously passed as a substring of the
  prohibition it contradicted.
- The style frontmatter pin now checks that the block parses
  the way the host reads it. A duplicate key or an unbalanced
  bracket previously passed the spelling pin while the host
  loaded the style with no fields set and force silently off.
- The derivation names the stamping section of the canonical
  skill text among its sources, where it previously narrowed
  the source list to four sections while carrying a sentence
  from the fifth.
- Decision 9 no longer claims other hosts silently ignore or
  hard fail unrecognized frontmatter fields. That behavior has
  no primary source on record, so the record treats it as
  unknown, with hard fail documented only on Anthropic's own
  distribution paths.
- The Cursor brief no longer carries the desktop client
  run as owed. A desktop verification run on 2026-10-25
  ran the official Cursor desktop build 3.27.12 on this
  box and settled the desktop load and duplicate
  registration questions, and the brief, decision 19, the
  eval corpus round 22 note, and the Cursor gate pins
  now record that evidence, with invocation precedence,
  marketplace installation, and Bugbot behaviour on a
  real pull request still open.
- The Cursor brief no longer carries invocation
  precedence as open on every surface. A live session
  run on the agent CLI surface on 2026-10-25 settled
  precedence on that surface, invoking the workspace
  copy in the shipped state and the added copy under
  .cursor/skills in the duplicate state, with the
  installed plugin copy registered and never invoked
  in either state, and the brief, decision 19, the
  eval corpus round 22 note, and the Cursor gate pins
  now record that evidence, with precedence open on
  the desktop client alone and marketplace
  installation and Bugbot behaviour on a real pull
  request still open.
- The README no longer states that the Cursor plugin
  is distributed through the Cursor Marketplace. It
  states that the plugin ships in this repo as a
  plugin package and that no Cursor Marketplace
  listing exists or has been submitted, with the
  local load as the route. The Install section no
  longer carries the copyable scoped npm test form
  for a package that does not exist, whose
  conditional draft form stays in the Qwen brief,
  and the paired eval claim now carries the
  construction caveat that a defect in an unchanged
  file is unreachable by a raw diff pass by
  construction. The Cursor gate and the Qwen gate
  and the eval gate now pin the corrected wording,
  and the Cursor gate refuses the stale marketplace
  distribution claim outright.
- The plugin README under `.cursor-plugin` no longer
  states that the Cursor plugin is distributed
  through the Cursor Marketplace. It states that
  the plugin ships in this repo as a plugin package
  and that no Cursor Marketplace listing exists or
  has been submitted, with the local load as the
  route. This correction is the addendum to the
  visual round 1 README correction. The Cursor gate
  now pins the corrected wording in that file and
  refuses the stale marketplace distribution
  wording there as well as in the root README.
- The README first screen is rebuilt as the
  storefront of the repo. The headline that a
  review starts from evidence instead of a bare
  diff now stands under the title, followed by the
  one canonical description, a one line navigation
  row linking the sections of the page, and a badge
  row of the CI and license badges alone. The hero
  recording carries a shortened alt text, the
  paired eval proof stands directly under it with
  its link and its construction caveat whole, and a
  one line install pointer closes the screen. The
  serving paragraph moved down to the Why section
  rather than leaving the page. Every display
  description in the repo now carries the canonical
  sentence, in the README and AGENTS.md openings,
  the plugin and marketplace manifests, the ZCode
  and Antigravity and portable package manifests,
  and the Cursor plugin README opening, while the
  skill frontmatter description stands as the named
  exception because its trigger sentences are the
  text a held out trigger run rewarded and no local
  trigger runner exists to retest a replacement.
  The static version badge left the README, and the
  version gate now proves coherence against the
  manifests and this changelog alone. The brief
  references in the adaptations table are now
  clickable relative links, and the description
  pins and the storefront pins in the gate tests
  moved with the wording.
- A typechange no longer shifts every later file onto the
  wrong diff body and a typechange with content on both
  sides can verify again. Git emits a typechange as two diff
  sections under one header while the name status output
  holds one entry for it, and the extractor paired sections
  with entries by position, so one extra section moved every
  later pairing by one and a verified packet could show one
  file's creation under another file's name while dropping
  a third file's diff entirely. Sections are now grouped
  by header identity before pairing and the two halves of a
  typechange stand merged under their own file, the line
  counter restarts at the second section header, and a diff
  whose grouped sections still cannot be paired with the
  name status entries fails closed instead of guessing.
- The blame reader in the history tier now refuses text
  conversion and external diff drivers like every diff
  invocation, and configuration supplied through the
  GIT_CONFIG environment variables no longer reaches any
  child process. A textconv driver named by the attributes
  of the reviewed tree and defined in clone configuration
  previously ran during a default extraction and rewrote
  the blamed content lines in the packet evidence, and the
  same driver defined through the environment fired as
  well. The line history reader, the blob reader and the
  companion search carry the same refusals, and every git
  child now runs with the pager disabled and with the
  caller supplied driver variables scrubbed from its
  environment. The packet check and eval gate scripts run
  their git children under the same scrub.
- The test vacuity guard no longer credits an assertion a
  test cannot fail on. Helper bodies are judged by the same
  rules as test bodies, a name bound to a literal in one body
  counts as a constant at the assertion, assertions after a
  return or inside a handler that swallows the assertion
  error no longer count, and asynchronous methods and files
  under the runner discovery patterns stand under the guard.
  The success line now names the limits recorded in the
  guard docstring instead of claiming more than it proves.
- The discovery fields each manifest schema allows, filled on
  the Claude and Cursor surfaces. The Claude manifest carries
  a display name and a homepage and a repository and a keyword
  set, its marketplace entry carries the category and the
  search tags its schema names there, and the Cursor manifest
  carries the same display name and homepage and repository
  and keyword set beside its own category and tags. A new
  discovery gate pins every value and the agreement of the
  two surfaces.
- Session screenshots for the packet output style and the
  reviewer persona. Two real Cursor agent sessions over the
  docs depth range were recorded under the capture discipline
  of the demo record, and stills from them stand in the
  packet output style section of the README and in the
  reviewer persona brief, with the full record filed beside
  the demo capture record.
- Submission packs for the three directories, prepared and
  evidence checked, with nothing submitted. The Cursor pack
  holds the marketplace filing route and the requirement set
  from the primary Cursor pages, with the evidence check met
  and two open points recorded where the primary sources
  conflict or stay silent. The Claude pack holds the
  directory portal route, the validation and policy
  obligations, and the evidence check, with the listing URL
  choice, the three examples gap, and the privacy
  determination recorded as open for the owner. The Agent
  Plugins pack records that the project runs no directory of
  packages, checks the portable package against its
  specification, and prepares the Awesome Copilot host
  listing, whose one prerequisite is the release tag only the
  owner can cut. A new gate pins the packs and the manifest
  facts their evidence checks rest on.
- The packet check is now a verifier rather than a structural
  reader. It reads the manifest with a strict reader that
  refuses a repeated key, validates the manifest against the
  packet manifest schema that now ships at
  `scripts/packet-manifest.schema.json`, rejects a verified
  claim whose own discrepancies list is not empty, and
  confirms the recorded base, head and merge base against the
  repository itself, with expect flags that let a reviewer
  name the range the stamp must cover. It recounts the
  recorded change from the repository through the extractor
  code and requires every file record and exclusion receipt
  to match the recount, and it reads the packet body against
  the manifest and the recount across the header, the
  contents totals, the triage list, numstat block and commit
  list, the change tier sections and diff bodies, the tier
  accounting and the closing receipt. A hand written packet
  could previously earn the verified stamp, and a genuine
  packet whose filename carries a Unicode line separator
  could never earn it, because the checker display path copy
  lacked the separator escapes. Both are fixed, and an
  adversarial name battery in the test suite holds the two
  display path copies to one behaviour.
- The packet check now also treats the packet directory as
  the sealed pair the stamp covers. A packet or a manifest
  standing as a symbolic link fails, and so does any further
  entry in the directory, including a whole nested packet,
  because the stamp covers the two files that live in the
  directory and nothing else. The packet is decoded as
  strict UTF-8, so a packet carrying a non UTF-8 filename
  byte, which no UTF-8 reader can open, no longer earns the
  stamp. The recorded extractor command is read back as
  well, so its mode flag must name the mode the manifest
  records and any full hash it carries must name the refs
  the manifest records.
- The Codex plugin build. The portable manifest gains the
  OpenAI extension with the interface discovery fields and
  the brand icon in the package assets, a repo marketplace
  at `.agents/plugins/marketplace.json` offers the package
  to Codex, and the skill folder gains `agents/openai.yaml`
  with implicit invocation left on and no tool dependencies.
  The Codex CLI on this box registered the marketplace,
  listed the plugin with its source at the package, and
  installed it into a scratch home cache with the package
  files inside, and invocation in a live Codex session stays
  unverified. A new gate pins the
  extension, the marketplace, and the skill folder file
  against the primary OpenAI documentation.
- The Build 14 Kimi hook contract is restated to the
  observation only truth the primary Kimi hooks page
  states. The four hook events TurnStarted, UserPromptQueued,
  TaskStarted and SessionHeartbeat carry the blocking column
  empty on that page, and only PreToolUse, Stop and
  UserPromptSubmit have return values that affect the main
  flow, so the brief and decision 24 no longer claim a
  blocking check on the four events and the gate no longer
  certifies one. The gate now pins the observation only
  posture and the blocking events list, forbids a blocking
  claim on the four events, and runs its live probe the way
  the host runs a hook. The fixture observation check reads
  the event from JSON on stdin with no arguments and exits
  0, where the shipped fixture read the event from argv and
  exited 1 in its fail mode, a code the host reads as a
  script error that defaults to allow.
- The extractor output directory is no longer cleared before
  a run is validated. Argument rejections and the new version
  flag leave every named output directory untouched, and the
  raw argument scan that chose a directory the parser had not
  chosen is gone. The inputs are resolved and read before the
  directory is opened, the output location is resolved once
  and pinned for the run, and the finished pair is staged
  inside the pinned directory and renamed into place under an
  exclusive lock, so a second run naming the same directory is
  refused while the first is working and a link swapped during
  the build cannot redirect or borrow the writes. A run that
  fails after its inputs were read leaves a failure receipt
  whose error field names the specific cause, a blocked output
  path reports the operating system reason instead of a bare
  refusal, and a run pointed at the root of a working tree is
  refused when tracked files named packet.md or manifest.json
  stand there. The packet check gained a version flag as well,
  and the smoke script now scrubs the git location environment
  like its siblings, so a stray GIT_DIR can no longer plant
  its fixture commits on another repository.
- The packet check now verifies the framing of a packet and
  not only the change inside it. The re-review section and the
  pull request preamble are rebuilt from the repository and
  from the records they stand on, the header and the contents
  block and the closing recount are compared whole against
  their rebuilds, and the range label is pinned against the
  recorded range spelling. The recorded command is read at the
  last value of every flag and its budget and tiers and
  findings values are pinned against the manifest, the cap
  notes list and the size of a dropped tier are recounted in
  the rebuild, and the budget account is checked against its
  own rules. The creation time must be a timestamp that does
  not name a moment after the check, a shallow clone refuses
  the stamp in its own words, a rebase in progress is named,
  and a packet or a manifest standing as a hard link fails
  for the reason a symbolic link fails. Display paths in the
  extractor and the check now escape bidirectional controls
  and zero width marks, so a crafted filename can no longer
  display as a different filename in a packet heading.
- A copied file is no longer labelled as renamed in a packet.
  The triage list and the change tier section name a copy with
  the copied wording and a rename with the renamed wording, and
  the packet check accepts the corrected wording and refuses
  the old mislabel in both places. The instruction file flag is
  judged from a copy destination path alone, so a copy taken
  from an instruction file under a plain name no longer carries
  the flag while a copy taken to an instruction name still does.
  Rename and copy detection now runs with no rename limit pinned
  on every git invocation, so a rename limit set in a clone or a
  global config can no longer switch inexact detection off, and
  a git warning that detection was skipped fails the run and
  reaches the failure receipt instead of being discarded. Copy
  detection also runs under the harder rule, so a copy whose
  source the change itself does not modify reads as a copy with
  its real line counts instead of as a plain addition.
- The remaining ambient configuration surface is pinned. The
  diff algorithm is pinned to histogram on every reader, so the
  numstat counts the manifest is built from and the diff bodies
  agree under any clone algorithm setting. Submodule pointer
  moves are always reported and always shown in the short form,
  so an ambient ignore or display setting can neither delete a
  submodule change from a verified packet nor rewrite its body
  or break its extraction. Shortened hashes stand at seven
  characters on the log lines, the diff index lines and the
  range diff output alike. Commit subjects are recoded to UTF-8
  under a pinned log output encoding, so a legacy encoded
  subject can no longer turn a verified packet into bytes that
  are not valid UTF-8. Attributes are read only from the tree
  under review, under an attribute source pin on every diff
  reading, a switched off user attributes file and a scrubbed
  attribute source environment, and the exclusion receipt now
  names that tree as the source of a marking. The one source
  no pin can confine, the attributes file inside the clone git
  directory, which git reads ahead of the tree itself, refuses
  the run and the packet stamp in plain words instead. Blame
  credit is confined the same way, with the configuration
  mailmap file switched off, the mailmap blob pinned to the
  mailmap file the reviewed head itself carries, the working
  tree mailmap out of reach of the reading, and the ignore
  revs list cleared, while a mailmap committed inside the
  recorded range still applies as reviewed content. The caller
  environment pathspec mode variables are scrubbed beside the
  driver family, so they can no longer break extraction on
  attribute marked files, the range diff stat fallback carries
  pinned widths, and the packet check reads and the extractor
  output probe carry the same pin list as every other
  invocation.
- The review chain no longer reads green on artefacts its
  author wrote alone. The fan out validator validates the
  packet manifest against the shipped packet manifest
  schema, reads the file list from the files key alone, and
  binds the record to the packet file standing beside the
  manifest, whose header and sections must match the
  manifest head, base and structure. Naming a repository
  adds the packet check recount and a line reading that
  refuses a finding location past the end of its file.
  Merged findings are proved by content, carrying the
  severity, summary, evidence, rule and location a raising
  review wrote, and merged evidence is read against the
  packet. Second pass findings obey the same packet
  evidence and dedupe rules as first pass findings, a new
  verdict may not reuse a merged finding id, verdict
  evidence must include the file the finding stands in, a
  note must carry substance, and every accepted second
  pass finding reaches the merged set, marked with the
  second pass as its source. A finding summary shaped as
  an instruction to a reviewer is flagged as steering
  content for a human to clear, and the fan out and
  headless docs name packet content as untrusted data.
- The headless gate reads the whole envelope. An error flag
  or an error subtype on any result message fails the run,
  a stream with more than one result message fails as a
  merged capture, a missing permission denials field fails,
  a permission denied system message anywhere in the stream
  fails, and a finding must cite at least one evidence path,
  carry a severity from the shipped vocabulary, and name a
  location inside the packet. The manifest is validated and
  refused when its verified flag is not true, the packet
  beside the manifest is compared against it, and a
  structured output naming a packet head must name the
  manifest head. The exit code is read from the exit file
  the invocation names, and a claimed exit code that
  disagrees with the record fails. The documented
  invocation passes the shipped headless findings schema
  as a schema value. A bridge script now carries a
  validated fan out run into a headless stream with its
  finding ids unchanged and its contested ids listed.
- A findings file now opens with a header naming its
  format version, the packet head it was written for, and
  the since anchor of its run, and the extractor refuses a
  file whose header names another run before any packet is
  built. The manifest records the hash of the findings
  file the run used, and the packet check compares a
  findings file standing at the recorded path against that
  hash and reads its header against the manifest head and
  since anchor.
- The packet check now rebuilds the change tier whole
  from the recount, so free prose inserted into that tier
  refuses the stamp. A packet whose Contents line is
  missing or damaged is refused rather than stamped with
  its header and contents rebuilds silently skipped. In
  pull request mode the check compares the base and head
  identifiers the GitHub CLI reports against the
  manifest, and a pull request body that cannot be read
  back and carries no cap line is refused rather than
  checked on presence alone. A relative findings path in
  the recorded command resolves beside the packet
  directory, in the directory that holds the packet
  directory, and never against the working directory the
  check was launched from. The manifest creation time is
  refused when it names a moment more than the stated
  allowance of one hour before the recorded head commit
  was committed or more than that allowance after the
  check runs. The extractor records the state of the
  pull request under review with the moment the fetch
  read it, in the packet and in the manifest, worded as
  a snapshot from that fetch and never as a live claim,
  and the history tier words the states of prior pull
  requests as a snapshot on the same terms.
- The token budget is now counted with a per shape token
  estimate priced by character class, replacing the rule
  that counted characters and divided by four and mispriced
  whole shape families by multiples, with CJK text priced
  near a quarter of its real cost and space runs near seven
  times theirs. On the shape families the audit measured, the
  real count lands between 0.49 and 1.35 times the estimate,
  so a measured family is never underpriced by a multiple and
  the emptiest family is overpriced by about twice at most. The shedding choice is cost aware, keeping
  the drop set that fits and keeps the most estimated tokens
  with history shedding before companions at equal kept size,
  so a budget that fits the small tier whole no longer sheds
  it under the fixed order. The refusal sentence names the
  true size of each core tier and of the smallest packet the
  selection can emit instead of blaming the core tiers for
  the whole shed packet, and the failure receipt a refusal
  leaves records the budget it was given, the measured size
  of that smallest packet, the tiers it would have dropped
  and what each tier would have cost. A budget under one is
  refused while the arguments are checked, matching the
  minimum the manifest schema records, and a budget refusal
  never replaces a standing verified packet with a failure
  receipt. The manifest records the prior pull requests
  passage of the history tier, and the packet check settles
  the size of a dropped history tier against that record, so
  an honest shed packet now stamps in any environment and
  not only in the one whose GitHub state built it. What did
  not change is the packet pair a successful run writes, the
  meaning of the verified flag, and the rule that the change
  itself is never truncated.

- The line counts are now read under the histogram algorithm
  at the numstat calls themselves, beside the pin every reader
  carries, and a regression test built on a file the two
  algorithms count differently holds the manifest counts and
  the recount of the diff body to the one reading. The packet
  over the WP1 landing range and the packet over the typechange
  pairing fix commit, the two ranges that failure stood on,
  verify. The re-review diff stat fallback is read under the
  same algorithm, so its counts cannot drift with ambient
  configuration.
- An attribute marked copy whose source also changed in the
  range is now measured by its own delta alone. Its per file
  re-measurement ran over the source path beside its own, and
  the source change rode into the copy's chunk, so the copy
  counted the source lines a second time and the packet
  verified with totals the change never made. The
  re-measurement now pairs its sections with its own name
  status output and keeps the section the entry owns, and a
  regression test holds the copy to its own counts.
- The severity vocabulary now stands as one vocabulary on
  every surface, P0 and P1 and P2 and P3, the set the
  shipped fan out and headless gates already enforced.
  The skill in all three copies, the packet output style
  and the reviewer persona state it in one shared sentence,
  with the persona gaining the sentence it lacked. The
  findings template in REVIEW.md gains a P0 heading above
  its P1 heading with a dated note, so reports written
  before the unification carry no P0 heading as record of
  their day and stand unedited. The fan out runbook states
  the vocabulary in prose for the first time, and both
  validator messages name the allowed values when they
  refuse one, where the fan out message once named none
  and the headless message named the vocabulary without
  its values. The shipped proof run keeps its historical
  P0 grade untouched and reads green under its own gate.
  A single pin in the test suite holds every surface to
  the set and classifies every file in the tree that
  names a severity, so a new surface cannot join in
  silence and a drift on a listed surface fails the gate.
- The change tier now sizes each per file diff fence one backtick
  longer than the longest backtick run inside the diff it fences
  with a floor of three, and the packet check reads that sized
  fence back under the same rule. A diff body holding a bare fence
  line as context, as a Markdown file holding a code block gives,
  closed the old fixed three backtick fence early and
  desynchronised the packet check, which then reported whole files
  as missing from a packet that held them and refused its stamp. A
  packet written under the old fixed fence still stamps wherever
  its diff bodies hold no run of three or more backticks anywhere,
  and a packet whose bodies hold such a run stamps once it is
  regenerated.
- The fan out validator now screens second pass notes against
  its steering phrase list beside finding summaries, with
  matching on collapsed text whose invisible separators read
  as spacing, and the screen now
  catches the freshly worded steering shape that asks for
  approval while asking for no defects to be mentioned, in
  the imperative form that shape takes, so a steering payload
  in a note and that summary shape no longer read green while
  descriptive prose about approval keeps reading green. The
  fan out runbook now names the screen as a listed phrase
  screen plus an imperative shape screen, so the contract
  states the control that stands behind it and no wider one.
- The packet check now refuses a findings hash on a packet whose
  recorded command carries no findings flag. A run with no
  findings file records no hash, so an invented hash on such a
  packet claimed a digest of an input the run never saw while
  the packet still stamped. The extractor now also clears any
  findings hash a reused run object might carry when a run names
  no findings file, so it cannot write such a manifest.
- The test vacuity guard no longer credits a fail call
  inside a conditional branch as a live assertion on its
  own. A test whose real assertion was softened to an
  always true one, leaving a trivial assertion standing
  beside a listing guard whose conditional fail once
  read as live to the guard, passed the guard in
  silence. Such a test now fails the guard by name, while
  a fail call outside every conditional branch still
  counts and a conditional fail beside a real assertion
  still passes.
- The test vacuity guard now reads a pure call over
  constants as a constant, so a test softened into a
  length or a conversion or a sort or a case form of
  literal values no longer passes the guard in silence.
  A builtin name standing as an operand counts as a
  constant beside the literal operands, and the same
  reading reaches a helper reached through an attribute
  call, a method whose first declared parameter is the
  receiver and not a call argument, called with a
  literal, so the first literal now binds to the real
  first parameter where it once bound to the receiver
  and left that parameter unbound. A call over a value
  keeps its credit in full, and so does a pure call over
  a name bound to a mutable container, because the
  container can gain contents the guard cannot see.
- The fan out steering screen now reads the rule field of a
  finding beside its summary, in the group reviews and the
  merged findings and the findings the second pass raises,
  so a listed phrase or an imperative shape carried in a
  rule no longer reads green while the same text in a
  summary is refused. The clause head shapes now admit the
  determiner forms of their approval object, naming the
  change or the pull request or the short pull request word
  with this or that or the or a or no determiner, and they
  now stand
  after a colon or an opening parenthesis and behind a
  comma with the word and or then, beside the heads they
  already admitted, while descriptive prose about approval
  done by a named subject and prose quoting a label as data
  and then naming that label with a subject verb keep
  reading green. The runbook passage and the validator
  docstring and the comment over the phrase list now name
  the screen as a listed phrase screen plus an imperative
  shape screen and state the four shapes and their clause
  head limit in words, so the contract states the control
  that stands behind it and no wider one.
- The fan out steering screen now admits a run of
  introducers at a clause head where it admitted one of
  each, so a shape opening with the words and then
  together or with two list markers or with the double
  asterisks of Markdown bold is refused in the positions
  where its single forms already were, and a doubled
  marker stacks with the conjunction run as well. Its
  suppression objects now stand in the singular beside
  the plural and its approval object now takes my or your
  beside the determiners it already took. Descriptive
  prose keeps reading green, including a label set in
  bold that a sentence names with a subject verb. The
  runbook passage and the comment over the patterns now
  state the runs and the added object forms in words.
- The test vacuity guard now reads a pure call over
  constants as a constant under four further spellings
  that settle the call in the text of the same body. A
  pure builtin called through a name the body bound to
  it or through the builtins module, a pure call inside
  a comprehension over a constant iterable, and a lambda
  called where it is written with constant arguments no
  longer pass the guard in silence. A lambda held in a
  name and called later keeps its credit, and so do an
  alias bound to anything but a pure builtin and a
  comprehension over an iterable the reading cannot
  settle and a comprehension whose element expression
  reads a mutable element of its iterable and a
  comprehension over a call outside the pure set such
  as a range call.
- The package gate now fails closed when the native
  plugin manifest stands in the tree but yields no
  version it can check the portable version against.
  A native manifest that cannot be read or does not
  parse or is not an object or carries no version or
  carries a version that is not a string now draws a
  named problem from the package gate itself. The
  version agreement reading once skipped in silence
  and the gate printed its holds line over the corrupt
  and empty and versionless and not an object shapes
  and over a manifest standing as a directory that it
  could not read. The non string version shape stood
  apart from that silence, because the disagreement
  sentence already noticed it and the gate exited
  nonzero, and an undecodable manifest stood apart as
  well, because the shipped helper let its decode
  error escape as a traceback. A genuinely absent
  native manifest keeps the single extension path
  problem it has always carried.
- A typechange whose blob is identical on both sides now
  verifies instead of failing its own recount. Plain
  numstat reports no added and no deleted lines for that
  shape because the bytes never changed, while the diff
  body shows the deletion of the old form and the
  creation of the new form and counts the lines those
  two sections carry. The extractor now records the
  body count for that one shape in both directions, so
  the manifest and the packet body and the recount tell
  one story and the packet still shows both forms with
  their modes. A typechange whose bytes differ in any
  way keeps the count numstat gave it, and a mode only
  change keeps its zero counts.
- Terminal escape sequences in packet content are now
  refused on both sides of the stamp. A diff body carrying
  colour or clear screen or OSC 8 hyperlink or window title
  sequences printed them raw in a verified packet, and a
  hostile findings file printed the same family raw in the
  prior findings accounting of a verified re-review packet
  through the file the packet check reads back as ground
  truth. The extractor now refuses to build a packet whose
  assembled text carries a terminal control character and
  refuses a findings file carrying one, and the packet
  check refuses to stamp such a packet and names the
  findings file ground in its own words. The refused set
  is the escape character, the C0 controls from U+0000
  to U+001F other than tab and newline, and the delete
  character, with a carriage return refused only where
  it stands alone, so tab characters and CRLF line
  endings in a genuine change still build and stamp.
  The C1 controls from U+0080 to U+009F stand outside
  the set for the reasons the verifier completeness
  reference states. No byte is
  stripped or rewritten on either side, because the packet
  body is evidence and a rewritten body would no longer
  be the bytes the recount counted.
- The packet check now refuses an invented findings hash
  on a since packet that carries no findings accounting
  where the manifest findings hash is not null and a
  findings flag appended to its recorded command names
  a file that cannot be read. The earlier reading
  refused a hash only where no findings flag stood, so
  one appended token disarmed it while the genuine since
  flag satisfied the pairing reading and the absent file
  meant the hash was never compared. A standing file
  whose bytes hash to a different value is refused on
  the same reading, while a packet that carries a
  findings accounting keeps the fallback reading on the
  findings its section itself carries.
- The headless review gate error flag reading now
  stands pinned by a test that isolates it. A single
  result message carrying the error flag alone with a
  success subtype and an empty denials list and a pass
  verdict earns the named error flag problem, and the
  same message with the flag clear reads green. The
  two review chain tests named for this shape now
  assert the error flag problem by name, so the error
  subtype reading and the merged capture reading can
  no longer satisfy them in the flag reading place.
- Regeneration over an existing verified packet is
  now conservative in both directions. A successful
  publish refuses before any rename when the output
  directory holds an entry the new packet does not
  receipt and leaves the standing pair untouched,
  apart from the findings file the run itself read
  from that directory, which the publish removes
  because the new packet already receipts its hash
  and its accounting. A failing regeneration now
  leaves a standing verified pair intact in the same
  way the budget refusal already did, whether the
  change is empty or the run inputs cannot be read
  or resolved, and reports its failure only in its
  exit code and its message.
- The readme and the extractor opening now state the
  regeneration preservation the code already carries.
  A failed run leaves a standing verified packet and
  its manifest untouched on every failure path and
  reports its failure in its exit code and its message,
  and a failure receipt is left only where no standing
  verified packet stands. The earlier readme sentence
  that a failed run removes an earlier packet first and
  the unqualified receipt sentence in the extractor
  opening are gone.
- The findings hash section of the verifier
  completeness reference now states the non null
  condition on its appended flag reading. The check
  holds the manifest hash to the file a findings flag
  names only where the manifest findings hash is not
  null, and a packet whose manifest records no hash
  draws no refusal from that reading.
- The bare word receipt no longer names two different
  artefacts on the front surfaces. The README and the
  examples note now call the manifest file the manifest
  receipt, and the skill text and the packet output
  style now name the closing section of the packet the
  closing recount receipt, so each use names the
  artefact it means.
- The package gate now refuses a manifest standing as
  a FIFO instead of hanging on the read. Both manifest
  readings test for a regular file before any read and
  follow links, so a link to a regular file still reads
  through and a link to a FIFO refuses the same way,
  and a manifest that stands in the tree but is not a
  regular file draws the named cannot be read problem
  at either manifest path. A dangling link keeps the
  absent reading at both paths, and a genuinely absent
  manifest keeps the behaviour it has always carried.
- The readme quickstart and the How it works diagram
  now state the same preservation. A failed run leaves
  a standing verified packet and its manifest untouched
  and reports its failure in its exit code and its
  message, and the two earlier wordings that a failed
  run leaves no packet standing are gone.
- The preserve default of the extractor failure publish
  now stands pinned by a test of its own. The test calls
  the failure publish on a standing verified pair without
  passing the preservation argument and asserts the pair
  stands untouched, so reversing the default fails the
  suite instead of passing in silence.
- The Claude submission pack now states the size of
  the largest file that is not an image or a font at
  238,810 bytes. The gate test file grew by 22 bytes
  when the readme preservation wording landed and the
  pack figure had kept the earlier size. The size
  limits item stands restated against the current
  tree, and the file stays the largest of its kind
  and stays under the cap the checklist holds.
- A copied entry measured as text through the binary
  measurement path now carries copy header lines in its
  diff body when its source was renamed away in the same
  range. The narrowed per file reading paired the source
  and the copy as a rename and the stored chunk kept that
  wording in both of its forms while the manifest and
  the packet prose said copied, so one packet presented
  one source as renamed to two destinations. The
  extractor now restores the header wording of the entry
  status the full range reading recorded and the counts
  stay unchanged, and the packet check now refuses a
  packet whose diff body copy or rename header wording
  disagrees with the status its manifest records for that
  section.
- The packet check now resolves its packet directory
  argument the way the extractor resolves its output
  argument so a spelling carrying a segment that does
  not exist followed by a parent segment reaches the
  same sealed pair at both doors.
- A directory or another special entry named as a
  publish staging file no longer survives a verified
  publish that its own packet check then refuses. The
  staging exemption in the publish path is now type
  aware and only a regular file or a link under a
  staging name is treated as a temp a killed run left
  behind and discarded, while any other staging named
  entry takes the same refusal branch as every other
  entry no manifest receipts, naming the entry and
  refusing the publish before any rename and leaving
  the standing verified pair byte for byte untouched.
- The gate scripts now refuse a file that is not a
  regular file at every remaining reading door instead
  of hanging when a FIFO stands there. The fan-out
  validator and the bridge refuse a non regular run
  record and a non regular manifest the record names,
  the headless gate refuses a non regular stream and
  manifest and exit file, and the package gate refuses
  a non regular brief, each with a named cannot be
  read problem and no read attempted. The same regular
  file test now stands in the shared reading helpers
  and the fixed path readings of the sibling gates,
  covering the brief and manifest and record readings
  of the Codex, Codex plugin, discovery, submissions,
  persona, mod, version and vacuity gates, while a
  link to a regular file still reads through
  everywhere and an absent path keeps the behaviour
  it has always carried.
- The Qwen Code brief now gives the build list for the
  Qoder test input its install route names. Rule R4
  states that the input is a new folder named qoder-input
  at the root of the checkout, carrying a manifest at
  its .qoder-plugin/plugin.json path with the name and
  version and description fields and the skill files
  under skills/recognitio, being SKILL.md and
  scripts/extract.py copied unchanged from the canonical
  skill tree, in the shape of the round 33 test input
  the brief records in rule R7. The Claude submission
  pack now states in its component paths evidence item
  that the privacy policy URL field also stands absent
  from the shipped manifest, pending the privacy
  determination the pack records.
- The Claude submission pack now states the repo
  holds 221 files. The FIFO sweep landing added the
  doors test file after the last restatement and the
  pack figure had kept the earlier count. The size
  limits item and the credential scan sentence stand
  restated against the current tree, and the count
  stands under the cap the checklist holds for a
  reviewer at 291 files of headroom.
- The principles page bullet in the Added section above
  now names the Going deeper section as the section the
  README links the page from. The storefront rebuild
  moved the link into that section and its own bullet
  records the move, and the principles bullet still
  named the Why section the link first stood in.
- A staging named entry recreated during a publish
  no longer rides into a verified publish its own
  packet check then refuses. The publish now lists
  the output directory again after its renames and
  again after it removes the entries it read, and
  any entry standing beyond the sealed pair at
  either reading takes the same refusal as every
  other entry no manifest receipts, naming the
  entry and putting the pair that stood there
  before the publish back byte for byte before it
  refuses. A staging name earns no exemption at
  that reading, because the stale staging discard
  already ran, so a regular file or a link
  recreated under a staging name during the
  publish refuses in the same way as a directory
  or a FIFO.
- The extractor now refuses a findings file that is
  not a regular file instead of hanging on the read.
  The findings reading tests for a regular file before
  any read and follows links, so a link to a regular
  findings file still reads through and a link to a
  FIFO refuses the same way, and a findings path
  standing as a FIFO or a directory draws the named
  cannot read problem at exit 2. The clone attributes
  reading and the standing manifest reading in the
  output directory stand behind the same regular file
  test, so a FIFO standing at either of those paths
  can no longer block a run or its failure receipt.
- The headless review page now prints the findings
  schema in the shipped shape. Its printed block carries
  the additional properties refusal at the top level and
  inside the finding object, matching the schema file
  the invocation hands the host, and the headless test
  now compares the printed block against the shipped
  schema in full shape, so a run built to the printed
  contract is no longer refused for an extra field the
  page never named and a future drift between the page
  and the file fails the suite.
- The eval gate and the regeneration gate now refuse
  a file that is not a regular file at every artefact
  reading door instead of hanging when a FIFO stands
  there. Every reading in both scripts now stands
  behind one guarded helper per script that tests
  existence first and the regular file shape second
  and only then reads, raising the same unreadable
  shape their callers already turn into their own
  cannot be read problems, so the shipped packet
  manifest and packet and sources and diff readings
  of the eval gate and the examples index and packet
  length readings of the regeneration gate refuse
  promptly in the wording each site already carried,
  while a link to a regular file still reads through
  and an absent path and a dangling link keep the
  behaviour they have always carried.
- The Claude submission pack now states the repo
  holds 222 files. The residual doors landing added
  the test file tests/test_fifo_residual_doors.py
  after the last restatement and the pack figure had
  kept the earlier count. The size limits item and
  the credential scan sentence stand restated against
  the current tree, and the count stands under the
  cap the checklist holds for a reviewer at 290
  files of headroom.
### Removed

- The 1.3.0 release draft and its highlights graphic are
  retired. The draft named a release base that later
  landings had already replaced, and five audit rounds
  indicted it without a repair ever landing, so its facts
  moved faster than its repair cycle. A fresh draft will
  be written just in time when a head is named for
  tagging, gated at that head, with the post publish
  record updates built into its checklist from the start.
  The prepared topics list the retired draft carried is
  preserved here so a future draft can start from it.
  The 17 topics are `agent-skills` and `ai-agents` and
  `claude-code` and `code-review` and `diff` and `git`
  and `pull-request` and `python` and `codex` and
  `cursor` and `github-copilot` and `coderabbit` and
  `devin` and `qwen` and `kimi` and `zcode` and
  `antigravity`. Seven of them stand live on the
  repository today, namely the first seven in that list,
  and `python` stands among the ten additions rather
  than among the kept topics.
- The demo builder at `docs/images/build_demo.py` and its
  capture file at `docs/images/capture.json`. The builder
  wrote only retired asset names, and the landing that
  retired its assets removes the builder with them.
- The dropped output problems wrapper in the regeneration
  gate. No gate run or test could reach it, and the live
  builder reading performs the same work inline at its
  own site, so the gate now holds one spelling of the
  reading and no dead one beside it.
- The five dead path constants at the head of the package
  gate and the package root constant they hung from. No
  code in the gate loaded any of them, and every function
  in the gate builds the paths it needs from the root
  argument it is handed, so the gate now holds one
  spelling of each path and no dead one beside it.
- The three dead constants in the Kimi gate, being the
  brief path and the decisions path at its head and the
  primary citations tuple further down with the comment
  that described it alone. No code in the gate loaded any
  of them, and every function in the gate builds the paths
  it needs from the root argument it is handed and screens
  a derivation note citation by the page path the note
  names, so the gate now holds one spelling of each path
  and no dead one beside it.
- The five dead constants in the ZCode gate, being the
  brief path and the plugin manifest path and the home
  manifest path and the skill path and the decisions
  path at its head. No code in the gate loaded any of
  them, and every function in the gate builds the paths
  it needs from the root argument it is handed, so the
  gate now holds one spelling of each path and no dead
  one beside it.
- The twenty six dead constants across seven provider
  gates, being the brief and decisions paths in the Codex
  and CodeRabbit and Antigravity and Copilot gates with
  the allowed sources tuple and the comment that
  described it alone in the Codex gate, the nine paths at
  the head of the Cursor gate with the plugin directory
  path that only those nine loaded, the brief and skill and
  decisions paths in the Devin gate, and the brief and
  decisions and changelog and readme paths with the
  figure words string in the Qwen gate. No code in any
  of the seven gates loaded any of them, and every
  function in those gates builds the paths it needs from
  the root argument it is handed, so each gate now holds
  one spelling of each path and no dead one beside it.
