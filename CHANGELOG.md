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
  plugin scope, the four hook events each carry a blocking check,
  the limits are 32KB per `systemPrompt` field and 64KB total,
  unsupported runtime fields appear as diagnostics, and print
  mode CI runs under the reviewer persona. The gate at
  `scripts/check_kimi.py` pins every rule's derivation note and
  the six adversarial pins the round 27 red team proved, with a
  live blocking test over the four hook events. Decision 24
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
  linked repository figure above 20. The ZCode gate
  rejects an execution claim for the registered fields
  and a description cap above 1024 characters. The Qwen
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
