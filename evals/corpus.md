# Eval corpus from real failures

This index encodes the incidents the audit program actually
found, from the first cycle through round 12, with each round
in its own section below, and maps each one to the
regression test or fixture that now covers it. A test name in this file was checked against the suite in the same
change that wrote the line. When a fix lands without a test, the
incident is recorded here as uncovered, with the gap stated in
the open, and that gap is the finding the next round should
raise.

The corpus is an index today rather than a second suite, because
the incidents already live as regression tests in the suite that
the gate runs. Its job is to keep the mapping visible, so a
reader can walk from a failure story to the test that guards it
without reading three audit reports first.

## Cycle 1 incidents

| Incident | Covered by |
| --- | --- |
| Paths that git quotes dropped out of the packet | `test_unicode_filename_keeps_its_change` in the extractor suite |
| Ambient git configuration reshaped the diff | `test_noprefix_and_colour_config_do_not_hide_the_change` and `test_external_diff_driver_is_not_used` in the extractor suite |
| Non UTF 8 content crashed the extractor | `test_latin1_source_does_not_crash` in the extractor suite |
| Pull request mode fell back to a same named local branch | `test_pr_with_unfetched_head_fails_loudly` in the extractor suite |
| A shallow clone was trusted | `test_shallow_clone_is_refused` in the extractor suite |
| A failed run left a stale verified packet standing | `test_failed_run_replaces_the_previous_verified_packet` in the extractor suite |

## Cycle 2 incidents

| Incident | Covered by |
| --- | --- |
| Replace refs swapped the reviewed content under a verified stamp | `test_replace_ref_cannot_swap_the_reviewed_content` in the extractor suite |
| The line recount mistook content lines for diff headers | `test_removed_sql_comment_verifies` and `test_added_toml_delimiter_verifies` in the extractor suite |
| Attribute marked files rested on one counter | `test_attribute_marked_sql_counts_are_cross_checked` in the extractor suite |
| Per file measurement passed raw pathspecs and glob names borrowed a neighbour diff | `test_renamed_attribute_file_is_measured_as_its_delta` and `test_glob_named_file_shows_its_own_diff` in the extractor suite |
| The re-review range diff ran without the textconv pins | `test_range_diff_cannot_be_rewritten_by_a_textconv_driver` in the extractor suite |
| Companion searches omitted attribute marked files and reported that nothing exists | `test_call_sites_found_when_tree_marks_sources_binary` in the extractor suite |
| GitHub CLI failures escaped as tracebacks | `test_missing_gh_fails_with_a_receipt_not_a_traceback` and `test_gh_view_returning_a_list_fails_cleanly` and `test_gh_list_with_wrongly_shaped_files_degrades` in the extractor suite |
| A failure inside argument parsing left the old packet standing | `test_invalid_tiers_clears_the_previous_verified_packet` in the extractor suite |
| A generated marker arriving in the change exempted its own file | `test_marker_arriving_in_the_change_is_shown_and_flagged` in the extractor suite |
| Pull request body text broke out of its fence and forged sections | `test_forged_completeness_section_stays_inside_the_fence` in the extractor suite |
| A thin packet could wear a full packet manifest | `test_a_thin_packet_wearing_a_full_manifest_fails` and `test_a_manifest_without_sections_fails` in the gate script suite |
| An empty findings file vanished without a trace | `test_empty_findings_file_is_named_in_the_packet` in the extractor suite |
| Findings accounting was uncapped and spawned a subprocess per finding | `test_findings_accounting_is_capped_and_states_it` in the extractor suite |
| The exclusion receipt listed one file twice with contradictory flags | `test_attribute_marked_lockfile_gets_one_receipt_entry` in the extractor suite |
| The copy gate claimed surfaces it never scanned | `test_em_dash_in_issue_template_config_is_caught` in the gate script suite, with a sibling catch test for each surface class |
| A both shed budget packet could land over its budget | `test_budget_sheds_t3_then_t2_and_stays_inside` in the extractor suite |

## Round 1 incidents

| Incident | Covered by |
| --- | --- |
| The packet checker read the head through an unscrubbed environment, so a GIT_DIR swap flipped its verdict | `test_exported_git_dir_does_not_redirect_the_packet_check` in the gate script suite. The fix landed with the cycle 2 set and this index records it here because round 1 is where the attack was filed |
| A newline inside a filename forged packet sections in a verified packet | `test_newline_filename_content_change_verifies_honestly` and `test_rename_into_a_newline_filename_forges_nothing` in the extractor suite |
| The same crafted name corrupted line counts through numstat record truncation | `test_newline_filename_content_change_verifies_honestly` in the extractor suite, which pins the counts at plus 1 and minus 1 |
| Findings anchored to paths that never existed were counted as addressed | `test_never_existed_paths_read_unaddressed` in the extractor suite |
| A binary to text transition was receipted as marked binary by repository attributes | `test_transition_receipt_and_no_raw_nul_in_packet` in the extractor suite |
| Raw NUL bytes from the old binary blob landed in the packet | `test_transition_receipt_and_no_raw_nul_in_packet` in the extractor suite |
| Generated packet prose carried banned marks from the extractor strings | `test_packet_over_binary_and_generated_changes_is_clean` and `test_packet_over_a_rereview_is_clean` in the extractor suite |

## Round 2 incidents

| Incident | Covered by |
| --- | --- |
| A cap note printed a raw path and a crafted filename forged a packet section again (R2-01) | `test_imports_cap_note_cannot_forge_a_section` in the extractor suite |
| The companion search parser split NUL delimited output on lines and a newline in a filename moved its hits onto another file (R2-02) | `test_grep_lines_attribute_a_newline_named_file` and `test_packet_names_the_crafted_test_file_and_its_lines` in the extractor suite |
| The version gate crashed with tracebacks on wrong typed JSON instead of naming the problem (R2-03) | `test_wrong_typed_versions_are_problems_not_crashes` and `test_main_reports_wrong_typed_shapes_without_a_traceback` in the gate script suite |
| The version gate passed a marketplace listing that listed nothing and accepted a leading zero version (R2-04) | `test_an_empty_or_missing_plugins_list_is_a_problem` and `test_a_leading_zero_version_is_not_a_version` in the gate script suite |
| The changelog version search was not scoped to the unreleased section (R2-05) | `test_a_decoy_carries_phrase_in_a_release_note_loses` in the gate script suite |
| Duplicate findings entries counted as separate findings and could crowd a real finding past the cap (R2-06) | `test_duplicates_cannot_crowd_out_a_unique_finding` and `test_dedupe_findings_keeps_first_of_each` in the extractor suite |
| Companion gathering grew faster than the change and a large packet took minutes (R2-07) | `test_build_t2_runs_one_grep_however_many_files` in the extractor suite |
| The copy fence again sat narrower than its claim and the authored evals files and the manifest descriptions stood outside it (ST2-01) | `test_discovery_extends_to_a_new_markdown_file_by_rule` and `test_em_dash_in_a_manifest_description_is_caught` and `test_fence_covers_every_authored_prose_file_in_the_tree` in the gate script suite |
| The marketplace entry lacked the researched skills list and the plugin manifest lacked an owner email (EX2-04) | `test_marketplace_lists_the_plugin_with_its_skill_path` in the gate script suite and `test_plugin_manifest_carries_the_owner_email` in the gate script suite |

Eight round 2 fixes stand as records only with no test of
their own, and this section records them as uncovered in the
open under the rule at the head of this file. The two long
extractor functions were split with no behaviour change
(ST2-02). The docs update map gained pairings for the review
guidance and the evals and the plugin listing (SP2-01). The
corpus index recorded the round 1 branch convention finding
as uncovered in its disclosure section (SP2-02). The
corpus index gained its statement of the path to a runnable
corpus and decision 3 recorded the remaining deferral
(EX2-03). The paired eval gained its clean control task and
its published run notes and its fair raw condition as records
in the evals documents (EX2-01). The trigger set near misses
were rewritten and scored in two passes as a record in the
trigger results file (EX2-02). The review guidance gained
its summary first report template (EX2-05) and the readme
first screen gained its bare list of what the tool does
(EX2-06). Each of those repairs is prose or a fixture or a
record, and no test pins any of them.

## Round 3 incidents

| Incident | Covered by |
| --- | --- |
| One test line printed once per term that matched it and the duplicates crowded the matches cap (RT3-01) | `test_a_line_matching_several_terms_prints_once_before_the_cap` in the extractor suite |
| The bulk term matcher waived the boundary check at any end of a term outside the ASCII word set and gained hits the per term grep rejects (RT3-02) | `test_term_matches_line_holds_non_word_edges_to_boundaries` and `test_bulk_search_agrees_with_per_term_grep_on_edge_terms` in the extractor suite |
| The version gate shape admitted Unicode digits, so a version written with an Arabic Indic digit passed as coherent (RT3-03) | `test_a_unicode_digit_version_is_not_a_version` in the gate script suite |
| The YAML half of the copy fence stayed a two file hand list while the claims promised discovery by rule (ST3-01) | `test_discovery_extends_to_new_yaml_files_by_rule` and `test_a_new_yaml_issue_form_joins_the_fence` in the gate script suite, with the completeness walk in `test_fence_covers_every_authored_prose_file_in_the_tree` extended to the YAML class |
| The completeness test walk encoded exclusion rules that contradicted the discovery exclusions (ST3-02) | `test_the_walk_and_discovery_share_one_exclusion_rule` in the gate script suite, with the walk and the discovery both calling the shared `is_fence_excluded` predicate in the copy gate |
| The eval runner note still described the two pass method after round 2 moved to three conditions plus a clean control (SP3-01) | `test_the_runner_note_describes_the_current_method` in the gate script suite |

## Round 4 incidents

| Incident | Covered by |
| --- | --- |
| A paired rename dropped the old module name from the companion search and the test files section could print a false absence (R4-01) | `test_companion_terms_include_old_stem_only_for_renames` and `test_old_name_only_importlib_line_is_found_after_a_rename` and `test_cap_note_names_the_test_file_for_old_stem_hits` in the extractor suite, with `test_ordinary_change_still_finds_its_test_mentions` in the extractor suite as the ordinary change control |
| YAML structure was judged as prose by the copy fence on the flow mapping and nested sequence shapes (R4-02) | `test_a_flow_mapping_value_is_structure_not_prose` and `test_a_nested_sequence_of_mappings_is_structure_not_prose` in the gate script suite, with `test_a_prose_mapping_value_with_a_colon_still_flags` and `test_a_prose_value_in_a_nested_sequence_still_flags` and `test_a_colon_inside_a_flow_mapping_value_still_flags` and `test_a_colon_inside_a_list_item_flow_mapping_still_flags` in the gate script suite pinning that prose values still flag |
| A findings entry written with a leading ./ counted as a second finding with the opposite verdict (R4-03) | `test_parse_and_dedupe_normalise_a_leading_dot_slash` and `test_dotted_pair_counts_once_with_one_verdict` in the extractor suite |

Five round 4 repairs stand as records only with no test of
their own, and this section records them as uncovered in the
open under the rule at the head of this file. The corpus
index gained its round 2 section and completed its scope
through round 3 (N4-01). The paired eval gained a fresh eyes
rerun over all five tasks, recorded in the per pass notes
with totals that agree with the results file. Decision 3
gained its explicit event trigger for a runnable incident
suite in the decisions file and in the path section of this
index. The review guidance gained its statement of where
disposition counts aggregate and when they are read, and the
first populated review report written from the template
stands in the reviews folder under docs. The one finding
that report raised, a miscount and an omission in the new
round 2 section of this index, was fixed in the same change
as a record and no test pins it.

## Round 5 incidents

Round 5 was a planning round and raised no code incidents
of its own. Its two handoff findings were adjudicated in
round 6 and stand in the round 6 section as the skill size
guard row and the instruction file flag row. This section
stands so the head of this index can say that each round
has its own section and a reader can tell that round 5 was
checked rather than skipped.

## Round 6 incidents

| Incident | Covered by |
| --- | --- |
| A copy of a modified file overwrote the re-review ranges of its source file and flipped both verdicts in a verified packet (R6-RT-01) | `test_modify_plus_copy_packet_pins_both_verdicts` and `test_rereview_ranges_for_a_copy_entry_hold_no_source_ranges` and `test_modify_without_a_copy_control_is_unchanged` in the extractor suite |
| The plugin did not load through the marketplace route, because both manifests specified the skill while the marketplace entry set strict to false (R6-INSTALL) | `test_manifest_conflict_problems_names_the_broken_pair` and `test_manifest_conflict_problems_accept_the_loadable_pairs` and `test_the_real_manifest_pair_has_no_conflict` in the gate script suite, with `test_marketplace_lists_the_plugin_with_its_skill_path` in the gate script suite pinning the strict entry in the shipped listing |
| A scalar spanning lines escaped its colon when the continuation line was shaped like a key (R6-01) | `test_a_key_shaped_continuation_of_a_quoted_scalar_still_flags` and `test_a_key_shaped_continuation_of_a_plain_scalar_still_flags` and `test_a_key_shaped_line_inside_a_flow_quoted_scalar_still_flags` in the gate script suite |
| Whole classes of YAML structure were still judged as prose, across wide key shapes and flow collections standing after anchors or tags or inside flow sequences (R6-RT-04 and S6-03) | `test_wide_key_shapes_are_structure_not_prose` and `test_flow_collections_after_anchors_and_tags_are_structure` and `test_a_flow_sequence_of_mappings_is_structure_not_prose` in the gate script suite, with `test_a_prose_value_after_a_wide_key_still_flags` and `test_a_prose_value_inside_a_flow_sequence_still_flags` and `test_ordinary_keys_after_a_plain_value_still_parse` and `test_a_multiline_flow_mapping_with_prose_values_still_flags` in the gate script suite pinning that prose still flags |
| Packets listed changed instruction files exactly like ordinary code, with no marker in the triage list and no field in the manifest (R6-RT-06) | `test_each_instruction_name_flags_and_an_ordinary_file_does_not` and `test_packet_flags_instruction_files_in_triage_and_manifest` and `test_a_rename_to_or_from_an_instruction_name_flags` in the extractor suite |
| Findings path normalisation stopped at a leading dot slash, so sibling spellings and a decomposed Unicode spelling each recounted one worry with a second verdict (R6-RT-02 and R6-RT-03) | `test_normalize_finding_path_covers_each_spelling` and `test_each_spelling_pair_counts_once_with_one_verdict` and `test_space_before_the_anchor_colon_counts_once` and `test_decomposed_path_counts_once_with_the_composed_file` in the extractor suite, with `test_distinct_line_and_distinct_file_still_count_separately` in the extractor suite as the distinctness control |
| No gate guarded the size of the skill file against host truncation (R6-RT-05) | `test_a_skill_file_past_the_size_limit_fails` and `test_a_skill_file_at_the_size_limit_passes` and `test_the_real_skill_package_is_valid` in the gate script suite |
| Two fence shapes behind the CodeRabbit answers on pull request 10, an apostrophe inside a plain flow scalar read as an opening quote and text standing after a closed flow collection left unscanned | `test_an_apostrophe_in_a_plain_flow_scalar_is_not_a_quote` and `test_text_after_a_flow_collection_still_flags` in the gate script suite |

Five round 6 repairs stand as records only with no test of
their own, and this section records them as uncovered in the
open under the rule at the head of this file. The stale
changelog sentence about a flow mapping value was repaired
as one prose sentence (R6-02). The corpus index gained its
round 4 section in this same change beside this section
(S6-01 and R6-E1). The populated round 4 review record
gained the identifiers its template requires in its checked
section (S6-02). The paired eval gained its replay task
task-06 with verbatim transcripts as records in the evals
documents, graded in the open as a designer run replay. The
one finding of the round 6 fix review record, a changelog
draft that claimed the review report before the report
stood in the tree, was repaired in the same change as a
record and no test pins it.

## Round 7 incidents

| Incident | Covered by |
| --- | --- |
| The manifest conflict gate failed a pair with no strict key that the host loads, because a missing key reads as true on the host (R7-RT-01) | `test_manifest_conflict_problems_follow_the_strict_states` in the gate script suite, with `test_manifest_conflict_problems_names_the_broken_pair` and `test_manifest_conflict_problems_accept_the_loadable_pairs` and `test_the_real_manifest_pair_has_no_conflict` in the gate script suite standing as they stood |
| The manifest conflict gate missed components declared under the experimental object of an entry while the host refused that pair (R7-RT-02) | `test_manifest_conflict_problems_cover_the_experimental_home` in the gate script suite |
| The instruction file flag missed the path specific Copilot instructions files and the Claude rules files that hosts load (R7-RT-03) | `test_path_specific_copilot_and_claude_rules_flag` and `test_near_miss_instruction_names_do_not_flag` and `test_packet_flags_the_new_instruction_surfaces` in the extractor suite |
| The skill size gate counted characters only, so a multibyte skill file passed while standing past a byte counting host cut (R7-RT-04) | `test_a_multibyte_skill_file_past_the_byte_limit_fails` in the gate script suite, with `test_a_skill_file_past_the_size_limit_fails` and `test_a_skill_file_at_the_size_limit_passes` and `test_the_real_skill_package_is_valid` in the gate script suite standing as they stood |
| A rename that flipped the line endings of a file marked every finding on it addressed in a verified packet (R7-RT-05) | `test_a_line_endings_only_rename_leaves_findings_unaddressed` and `test_a_rename_with_a_real_change_still_counts_it` in the extractor suite |

Three round 7 repairs stand as records only with no test
of their own, and this section records them as uncovered
in the open under the rule at the head of this file. The
changelog sentence about the manifest conflict check was
rewritten to state the shipped rule in the same change
(R7-02). The corpus index gained this round 7 section and
completed its round 6 section in the same change (R7-E1).
The round 7 fix review report stands in the reviews folder
as a record of this change and no test pins it.
The stateful YAML reader split into named helpers with no
behaviour change stands covered by
`test_no_function_in_check_copy_passes_the_length_ceiling`
in the gate script suite for its ceiling and by the whole
fence test set for its behaviour (R7-01).

## Round 8 incidents

| Incident | Covered by |
| --- | --- |
| No gate guarded the eval artefacts, so a quiet edit to a transcript fence or a planted grading rule or a recorded results cell left the gate green (R8-RT-01) | `test_a_transcript_edit_fails_naming_its_file` and `test_a_planted_rule_edit_fails_naming_its_file` and `test_a_results_cell_edit_fails_the_totals_check` and `test_a_tampered_diff_fails_the_rebuild` and `test_the_checksum_record_regenerates_and_then_passes` in the gate script suite, with `test_the_real_eval_artefacts_pass` in the gate script suite pinning the pristine tree and `test_a_task_with_crlf_sources_rebuilds_byte_for_byte` and `test_a_manifest_entry_missing_a_key_fails_the_rebuild` and `test_a_non_object_manifest_is_a_problem_not_a_crash` in the gate script suite pinning the rebuild shapes the CodeRabbit answers on pull request 12 hardened |
| No gate compared the corpus index against the suite, so a renamed test silently orphaned its rows (R8-RT-02) | `test_a_renamed_cited_test_fails_the_corpus_check` and `test_a_corpus_name_that_never_existed_fails` in the gate script suite, with `test_the_real_eval_artefacts_pass` in the gate script suite pinning the pristine index against the suite |
| A fixture teardown that met a genuinely unremovable tree raised out of cleanup after a bounded retry instead of passing in silence (CodeRabbit repair on pull request 12) | `test_cleanup_retries_a_removal_that_fails_once` and `test_cleanup_retries_when_a_child_path_vanishes_mid_removal` and `test_cleanup_raises_after_the_bound_when_removal_always_fails` in the extractor suite and in the gate script suite |
| The manifest entry comparison exempted a legacy key everywhere instead of only where no saved entry carries it (CodeRabbit repair on pull request 12) | `test_a_manifest_entry_key_missing_from_every_entry_fails` in the gate script suite |

Two more round 8 repairs stood as records only when this
section was first written and now map to tests in the table
above. The fixture teardown repair and the narrowed manifest
key exemption both landed as CodeRabbit answers on pull
request 12 after the review record was written, and the round
9 pass records them late rather than leaving the gap the
round 9 spec lane raised. Four round 8 repairs still stand as
records only with no test of their own, and this section
records them as uncovered in the open under the rule at the
head of this file. The
gate description and the current state text in AGENTS.md
gained their round 8 sentences in the same change. This
round 8 section itself stands as a record of the change.
The round 8 fix review report stands in the reviews folder
as a record of this change and no test pins it. The saved
packet text of each task also stands outside the rebuild
the gate runs, because the commit subjects and authors of
the original fixture commits stand in no sources file, so
the gate covers the saved packets with the checksum record
and with the section check of the packet checker and says
so in the open in the gate script.

## Round 9 incidents

| Incident | Covered by |
| --- | --- |
| The totals check guarded sums and headlines only, so a moved per task distribution and an upgraded task-06 transcript each passed after the documented checksum refresh (R9-RT-01) | `test_task06_scores_rederive_from_its_transcripts` and `test_an_upgraded_task06_transcript_fails_the_derivation` and `test_a_moved_task06_results_cell_fails_the_derivation` and `test_an_unparseable_task06_planted_rule_fails_closed` in the gate script suite, with the moved distribution over tasks 01 to 05 standing as a deliberate residual in decision 8 of the decisions file |
| The rebuild check anchored each task to its own sources file, so tampering the sources and regenerating the artefacts passed after a checksum refresh (R9-RT-02) | `test_tampered_sources_regeneration_fails_the_anchor` and `test_source_anchors_regenerate_and_then_pass` and `test_the_checksum_refresh_refuses_while_source_anchors_are_stale` in the gate script suite |
| A duplicate key in the checksum record silently overrode the pin with no refresh step at all (R9-RT-03) | `test_a_duplicate_key_in_the_checksum_record_fails` and `test_a_duplicate_key_in_a_sources_file_fails_the_rebuild` and `test_a_duplicate_key_in_a_saved_manifest_fails` in the gate script suite |
| The corpus check named only cited test names the suite lacks, and the corpus file itself stood outside the checksum record, so a dropped row or a quietly dropped citation passed the gate (R9-RT-04) | `test_a_dropped_corpus_row_fails_the_coverage_floor` and `test_a_dropped_corpus_citation_fails_the_coverage_floor` and `test_corpus_md_stands_in_the_checksum_record` and `test_corpus_coverage_regenerates_and_then_passes` in the gate script suite |
| The round 8 corpus section stopped two repairs short of the end of its own landing (R9-SP-01) | the completed round 8 section in this same change, pinned by the corpus coverage floor |
| A semicolon stood in the user facing tiers help text that no gate reached (R9-ST-01) | `test_help_output_carries_no_banned_marks` in the gate script suite |
| The checksum record keys used the host path spelling, so the gate failed on a pristine Windows tree and the refresh path would have rewritten the record in the local spelling (R9-EX-01) | `test_record_keys_use_posix_spelling` in the gate script suite |

Two round 9 repairs stand as records only with no test
of their own, and this section records them as uncovered
in the open under the rule at the head of this file. The
round 9 fix review report stands in the reviews folder as a
record of this change and no test pins it. The deliberate
residual over the tasks 01 to 05 score distribution stands
as decision 8 in the decisions file, and no test pins a
prose decision.

## Round 10 incidents

Round 10 was a research and plan refinement round and shipped
no code of its own. Its red team filed two findings against
the round 9 eval hardening, and both were closed by the round
11 landing.

| Incident | Covered by |
| --- | --- |
| The fence grader credited grading tokens anywhere in the transcript, so a score move plus a token plant passed the derivation the round 9 repair added (R10-RT-01) | `test_pristine_fences_grade_as_recorded` and `test_a_casual_filename_note_does_not_move_d1` and `test_a_doubling_denial_gets_no_credit` and `test_a_plus_side_overcount_gets_no_credit` and `test_kindred_doubling_words_credit` in tests/test_eval_anchors.py |
| The two summaries agreement branch of the task-06 re-derivation had no pinning test (R10-SF-01) | `test_a_single_summary_move_fails_the_agreement_check` in tests/test_eval_anchors.py |

One round 10 repair stands as a record only with no test of
its own, and this section records it as uncovered in the open
under the rule at the head of this file. The pushed commit
titles of the round 9 landing did not follow Conventional
Commits (ST-R10-01), and the round 11 landing closed the
finding by carrying the prefixes. No test pins a commit title.

## Round 11 incidents

| Incident | Covered by |
| --- | --- |
| Tasks 01 to 05 had no planted defect anchor, so a sources tamper that drops a planted defect passed the full documented refresh (R11-RT-01) | `test_task01_three_argument_tamper_fails_the_task_anchor` and `test_task_anchors_pass_on_the_real_tree` in tests/test_eval_anchors.py, with the per task effect probes in `TASK_ANCHOR_PROBES` in scripts/check_evals.py exercised by `test_the_real_eval_artefacts_pass` in the gate script suite |
| A shimmed task-06 head kept its planted defect out of reach while the transcripts still described it (R9G-RT-02, first shape) | `test_a_shimmed_task06_head_fails_the_d1_effect_anchor` in tests/test_eval_anchors.py |
| A commented doubling kept its planted defect out of reach while the transcript still described it (R9G-RT-02, second shape) | `test_a_commented_task06_doubling_fails_the_d2_effect_anchor` in tests/test_eval_anchors.py |
| A transcript that denied the defect in plain words still derived full credit (R9G-RT-03) | `test_a_doubling_denial_gets_no_credit` and `test_kindred_doubling_words_credit` in tests/test_eval_anchors.py |

Round 11 raised no spec or standards findings of its own, and
its Build 1 frontmatter widening passed every gate unchanged.

## Round 12 incidents

| Incident | Covered by |
| --- | --- |
| The skill description was spelled three ways with no text pin on any of them, so a clean rewrite of the trigger-tuned frontmatter description passed the full gate (R12-RT-01) | `test_frontmatter_description_is_pinned` and `test_plugin_manifest_description_is_pinned` and `test_marketplace_entry_description_is_pinned` in the gate script suite |
| A duplicate key in the packaging manifests was silently resolved to the last value by every gate reader (R12-RT-02) | `test_a_repeated_key_in_plugin_json_fails` and `test_a_repeated_key_in_marketplace_json_fails` in the gate script suite |
| The marketplace listing could carry a second plugin entry naming the same skill under a different name with the full gate green (R12-RT-03) | `test_marketplace_lists_the_plugin_with_its_skill_path` in the gate script suite, which pins the listing to its single entry |
| A wrong-typed strict key was silently read as strict true (R12-RT-04) | `test_a_wrong_typed_strict_key_is_a_problem` in the gate script suite |

One round 12 repair stands as a record only with no test of
its own, and this section records it as uncovered in the open
under the rule at the head of this file. The mode-only
follow-up commit title of the round 12 landing carried no
`chore:` prefix (R13-ST-01, filed in round 13), and the
convention in AGENTS.md now requires the prefix on every
pushed title going forward. No test pins a commit title.

## Disclosure incidents with no test of their own

Four prose only fixes stand in this position. Three spec
findings from the cycles were disclosure defects rather than
behaviour defects. The prior pull request lookup now states its
window in the packet and in the docs, the changelog carries one
Added group under its unreleased heading, and the receipt prose
defines what the files per tier counts count. No test pins any
of the three, and this index says so plainly instead of
inventing coverage. A future round can close the gap with a
docs test if the gap starts to matter.

The fourth is the round 1 branch convention finding, recorded
in the round 1 fix report as SP-R1-01. Its repair was prose and
a decision entry, the conventions in AGENTS.md and decision 7 in
the decisions file, and no test pins the branch conventions or
the vestigial standing of the dev branch. It is recorded here
as uncovered in the open, as the rule at the head of this file
requires.

## The path from this index to a runnable corpus

The path is short today. Each row above names a regression test
in the suite the gate runs, and running the gate runs the corpus
in that form. A separate suite that replays the incidents as
skill tasks is deferred, and decision 3 in the decisions file
records the deferral and its reason in the open. That decision
now also names the trigger for the lift. The rows become a
runnable suite at the first of a standalone tool decision, a
round that asks for findings per tier per token, or the close
of this audit program.
