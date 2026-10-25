# Eval corpus from real failures

This index encodes the incidents the audit program actually
found, from the first cycle through round 34, with each round
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

## Round 13 incidents

| Incident | Covered by |
| --- | --- |
| The corpus index stopped at round 9 while the program was at round 13, leaving the round 10 to 12 incidents unmapped to their regression tests (R13-RT-01) | `test_scope_cap_names_the_highest_round_section` and `test_a_stale_scope_sentence_fails_the_scope_check` and `test_a_section_past_the_scope_cap_fails_the_scope_check` and `test_a_skipped_round_fails_the_scope_check` in the gate script suite, with the round 10, 11 and 12 sections added in the same change pinned by the corpus coverage floor |

One round 13 repair stands as a record only with no test of
its own, and this section records it as uncovered in the open
under the rule at the head of this file. The mode-only
follow-up commit title of the round 13 landing carried no
`chore:` prefix (R13-ST-01), the same defect the round 12
section records on the round 12 follow-up, and the convention
in AGENTS.md now requires the prefix on every pushed title
going forward. No test pins a commit title.

## Round 14 incidents

| Incident | Covered by |
| --- | --- |
| The declared outputStyles path missed the shipped style file under the vendor's path rules, so the forced packet style never loaded on the host while the gate stayed green (R14-RT-05) | `test_style_path_resolves_against_the_plugin_root` and `test_the_old_layout_fails_the_vendor_resolution` in the gate script suite, with `test_style_file_exists_where_the_manifests_declare_it` in the gate script suite pinning the relocated file against the plugin root |
| The derivation section was skipped by the "no new instruction" sentence check, so a novel instruction or a non http external reference shipped with the gate green (R14-RT-01) | `test_style_derivation_is_the_pinned_prose` in the gate script suite, which pins the derivation word for word, with `test_style_claims_no_enforcement` in the gate script suite pinning the line-anchored region the B2 subheading plant first slipped |
| Substring matching let an imperative inversion of a pinned prohibition pass the sentence check (R14-RT-02) | `test_style_sentences_stand_in_the_canonical_text` in the gate script suite, which matches whole sentences instead of substrings |
| A duplicate frontmatter key or an unbalanced bracket passed the spelling pin while the host would load the style with no fields set, force silently off (R14-RT-03) | `test_style_frontmatter_is_host_readable` and `test_a_duplicate_frontmatter_key_is_a_readability_problem` and `test_an_unbalanced_bracket_is_a_readability_problem` in the gate script suite |
| The style pointer test asserted on an in-memory dict and never ran any gate code, so it could not fail for a real reason (R14-RT-04 and R14-ST-01) | `test_an_entry_missing_the_style_pointer_fails_the_pin` in the gate script suite, which plants the defect in real manifest files on a scratch tree and runs the real pin |
| The Build 4 plan definition named a permission denials signal in stream-json with no primary source, so the adversarial pass it specified could not be built against it (R14-EX-01) | the sourced denial signal in scripts/check_headless.py pinned by `test_permission_denials_fail_the_run` and `test_a_run_without_structured_output_fails` and `test_an_in_run_failure_printed_as_the_result_fails` in tests/test_headless.py, with decision 11 in the decisions file recording the correction |

Five round 14 repairs stand as records only with no test of
their own, and this section records them as uncovered in the
open under the rule at the head of this file. The derivation
source list gained the stamping section as prose (R14-SF-01).
Decision 9 was rephrased to state the evidence boundary on
other hosts' frontmatter behavior and the decision 10 path was
corrected (R14-EX-02). The round 14 fix review report stands in
the reviews folder as a record of this change and no test pins
it. The round 11, 12 and 13 fix review records were written
retrospectively in round 14 from their fix reports with the
caveat stated, and no test pins any of them.

## Round 15 incidents

Round 15 was a research and plan refinement round and
raised no code incidents of its own. Its plan handed
the Build 5, Build 6, Build 7, and Build 8 adaptation
builds to rounds 16 through 19, and the plan
corrections the round 16 audits raised stand in the
round 16 section as record items. This section stands
so the head of this index can say that each round has
its own section and a reader can tell that round 15
was checked rather than skipped.

## Round 16 incidents

| Incident | Covered by |
| --- | --- |
| The plugin reviewer persona shipped with no pin on its surface, so a widened tools allowlist and free push rights prose passed the gate (R16-RT-01) | `test_a_widened_tools_allowlist_fails_the_pin` and `test_the_pinned_persona_prose_is_word_for_word` in the gate script suite |
| The persona prose segmentation had no word for word pin, so a naive segmentation helper passed unnoticed (R16-ST-01 in the round 16 fix report series, not the round 16 standards lane report which reuses the same ID for mode only commit titles) | `test_the_pinned_persona_prose_is_word_for_word` in the gate script suite |

Two round 16 repairs stand as records only with no test
of their own, and this section records them as uncovered
in the open under the rule at the head of this file. The
plan-round15 section 2 correction (R16-RT-02) and the
Build 16 and Build 18 decision changes (R16-SF-01 and
R16-SF-02) are program record prose and decision entries,
and no test pins a plan sentence or a decision entry.

## Round 17 incidents

| Incident | Covered by |
| --- | --- |
| The extractor instruction file set missed the plugin agents folder, so a widened agent file read as ordinary code (R17-RT-01) | `test_a_plugin_agent_file_is_instruction_bearing` and `test_a_changed_agent_file_is_flagged_end_to_end` in tests/test_fanout.py |
| An undeclared agent file in the agents directory passed the persona gate (R17-RT-02) | `test_an_undeclared_agent_file_fails` in tests/test_fanout.py |
| The isolation pin read only the double quoted worktree form, and an empty disallowed tools list reported a misleading message (R17-ST-01) | `test_single_quoted_worktree_passes` and `test_double_quoted_worktree_passes` and `test_unquoted_worktree_passes` and `test_an_empty_disallowed_tools_list_names_itself` in tests/test_fanout.py |

## Round 18 incidents

| Incident | Covered by |
| --- | --- |
| A confirm or contest verdict naming a finding outside the merged set passed the fan-out validator (R18-ST-01) | `test_a_verdict_for_an_unknown_finding_fails` in tests/test_fanout.py |

One round 18 repair stands as a record only with no test
of its own, and this section records it as uncovered in
the open under the rule at the head of this file. The
struck onFailure correction in the round 10 plan and
research documents (R18-RT-01) is a program record
correction under the round 14 retrospective correction
convention, and no test pins a plan sentence.

## Round 19 incidents

| Incident | Covered by |
| --- | --- |
| A package carrying an mcp.json file passed the portable package gate, against the recorded omission disposition (R19-RT-02) | `test_a_present_mcp_json_fails` in tests/test_package.py |
| A drifted package skill copy passed the byte identity pin (R19-RT-03) | `test_a_drifted_skill_copy_fails` in tests/test_package.py |
| A Claude Code key at the top level of the portable manifest passed the closed schema pin (R19-SP-01) | `test_a_claude_code_key_at_the_top_level_fails` in tests/test_package.py |
| The copy fence hand listed manifests instead of discovering them by rule, so a new manifest stood outside the fence (R19-ST-01) | `test_manifest_discovery_extends_to_a_new_manifest_by_rule` in the gate script suite |

Four round 19 repairs stand as records only with no test
of their own, and this section records them as uncovered
in the open under the rule at the head of this file. The
plan-round10 Build 8 paragraph correction (R19-RT-01)
and the plan-round15 section 4 rewrite on the AAIF
donation (R19-EX-01) are program record prose. The AAIF
governance split and integrations naming (R19-EX-02)
stand as brief prose. The gate conventions repair
(R19-ST-02) is process prose. No test pins a plan
sentence or a convention.

## Round 20 incidents

Round 20 was a research and plan refinement round and
raised no code incidents of its own. Its plan handed
the Build 9, Build 10, Build 11, and Build 12
adaptation builds to rounds 21 through 24, and the
findings those rounds raised stand in their own
sections below. This section stands so the head of
this index can say that each round has its own
section and a reader can tell that round 20 was
checked rather than skipped.

## Round 21 incidents

| Incident | Covered by |
| --- | --- |
| A model pin without a surface scope passed the Codex brief gate (R21-RT-01) | `test_an_unqualified_model_pin_fails` in tests/test_codex.py |
| A monitoring claim without the default branch limit and a coverage claim without its limit passed the Codex brief gate (R21-RT-02) | `test_a_dropped_default_branch_limit_fails` and `test_a_dropped_coverage_limit_fails` in tests/test_codex.py |
| Two pauses with different meanings were conflated in the Codex brief (R21-RT-03) | `test_a_conflated_pause_fails` in tests/test_codex.py |
| A dropped no-calendar negative in the Security Cloud story passed the Codex brief gate | `test_a_dropped_no_calendar_negative_fails` in tests/test_codex.py |
| A dropped SECURITY.md policy context note passed the Codex brief gate | `test_a_dropped_security_md_note_fails` in tests/test_codex.py |
| Stale AAIF donation wording passed the package gate (R21-ST-01) | `test_a_brief_with_the_stale_aaif_wording_fails` in tests/test_package.py |

One round 21 repair stands as a record only with no test
of its own, and this section records it as uncovered in
the open under the rule at the head of this file. The
Guardian auto_review keys promotion and the review_model
and project_doc_max_bytes entries (R21-EX-01) stand as
brief prose with primary citations, and this section
names no pinning test for those entries by name.

## Round 22 incidents

| Incident | Covered by |
| --- | --- |
| A symlinked skill copy passed the Cursor plugin gate, against the real directory copy rule (R22-RT-01) | `test_a_symlinked_skill_copy_fails` in tests/test_cursor.py |
| An effort value written as a BUGBOT.md setting passed, against the Teams dashboard setting rule (R22-RT-02) | `test_a_dropped_effort_split_pin_fails` in tests/test_cursor.py |
| A dropped neutral default and a dropped fail on unresolved pin passed the Cursor plugin gate (R22-RT-03) | `test_a_dropped_neutral_pin_fails` and `test_a_dropped_fail_on_unresolved_pin_fails` in tests/test_cursor.py |
| A platform provided variable used as a schema variable passed the Cursor plugin gate (R22-RT-04) | `test_a_variables_schema_violation_fails` in tests/test_cursor.py |
| An unknown bugbot.yaml field passed the Cursor plugin gate (R22-RT-05) | `test_an_unknown_bugbot_yaml_field_fails` in tests/test_cursor.py |
| A dropped Security Review separation pin passed the Cursor plugin gate | `test_a_dropped_security_review_pin_fails` in tests/test_cursor.py |

The review latency risk (R22-RT-06) stays carried as an
unbounded risk in the brief and decision record, and the
real client run noted in the R22-RT-01 row stays owed
because no Cursor client runs on this box. The caps and
packaging rules (R22-RT-07 and R22-RT-08) and the half
primary pin and canvases sentence (R22-EX-01 and
R22-EX-02) stand as brief and decision record prose in
the same change, and this section records them without
a pinning test of their own.

## Round 23 incidents

| Incident | Covered by |
| --- | --- |
| A test with a vacuous body or an assertion that argues about nothing passed the suite (R23-RT-01) | `test_a_bare_pass_body_fails` and `test_an_always_true_assertion_fails` and `test_a_constant_equality_without_a_fixture_fails` and `test_an_assertion_without_a_fixture_touch_fails` in tests/test_vacuity.py |
| A Cursor plugin file stood outside the copy fence (R23-ST-01) | `test_em_dash_in_cursor_plugin_readme_is_caught` and `test_em_dash_in_cursor_plugin_rule_file_is_caught` and `test_em_dash_in_cursor_plugin_manifest_is_caught` in the gate script suite |
| A marketplace only version drift passed the Cursor plugin gate (R23-ST-02) | `test_a_marketplace_only_version_drift_fails` in tests/test_cursor.py |
| A focus or profile sentence naming no axis passed the CodeRabbit brief gate (R23-SP-A1) | `test_a_dropped_axis_naming_fails` in tests/test_coderabbit.py |
| A dropped summary fold pin passed the CodeRabbit brief gate (R23-SP-A2) | `test_a_dropped_summary_fold_pin_fails` in tests/test_coderabbit.py |
| A deeper analysis reading of high and a softened focus constraint passed the CodeRabbit brief gate | `test_a_deeper_reading_of_high_fails` and `test_a_softened_focus_constraint_fails` and `test_a_dropped_rename_direction_fails` in tests/test_coderabbit.py |
| A dropped guideline provenance pin and a dropped claude rules pin passed the CodeRabbit brief gate (R23-EX-01) | `test_a_dropped_provenance_pin_fails` and `test_a_dropped_claude_rules_pin_fails` in tests/test_coderabbit.py |

The vacuity guard limit stands as a recorded limit. The
guard catches vacuous bodies and not subtle tautologies
over fixture derived values, and the spec lane diff
review stays the guard for that shape. The Deep Scan
runtime verification sentence (R23-EX-02) was skipped by
choice, and the skip is recorded in the decision record
for a later round. The Build 13 citation upgrades
(R23-EX-03, R23-EX-04, and R23-EX-05) were handed
forward to round 26 and stand outside this section.

## Round 24 incidents

| Incident | Covered by |
| --- | --- |
| A native platform file inside the portable core passed the package gate (R24-RT-01) | `test_a_native_file_inside_the_portable_core_fails` in tests/test_package.py |
| A second extensions namespace with a dangling shape path passed the package gate (R24-RT-02) | `test_a_second_namespace_with_a_dangling_path_fails` and `test_a_dangling_antigravity_path_fails` in tests/test_package.py |
| A removed or corrupted PreToolUse hook file passed the gate while the manifest still declared it (R24-RT-03) | `test_a_missing_hook_file_fails` and `test_an_unparseable_hook_file_fails` and `test_a_hook_without_pretooluse_fails` and `test_a_hook_without_deny_fails` and `test_a_hook_without_force_ask_fails` and `test_a_hook_without_auto_approve_fails` in tests/test_antigravity.py |
| The deny, force_ask, and auto_approve harness contract stood without pins (R24-RT-04) | `test_a_dropped_deny_mapping_fails` and `test_a_dropped_force_ask_mapping_fails` and `test_a_dropped_auto_approve_mapping_fails` and `test_a_dropped_honest_limit_fails` in tests/test_antigravity.py |
| The Build 7 mod hooks were treated as portable although the primary hooks page names no agent.spawn event (R24-RT-06) | `test_a_dropped_claude_code_only_negative_fails` in tests/test_antigravity.py |
| A pinned page stamp reading passed the dated evidence gate although the sunset page stamp had drifted (R24-RT-02, dated evidence lane) | `test_a_pinned_page_stamp_reading_fails` and `test_a_dropped_sunset_halt_fails` and `test_a_dropped_contract_terms_fails` and `test_a_dropped_renewal_dates_fails` and `test_a_dropped_named_path_fails` and `test_a_dropped_v0_65_0_pin_fails` and `test_a_dropped_docs_lag_fails` in tests/test_antigravity.py |
| Dated evidence sentences stood without pins, so a quiet drop of the sunset date, the halt, or the docs lag caveat passed (R24-RT-03, dated evidence lane) | `test_a_dropped_pre_release_fails` and `test_a_dropped_extension_boundary_fails` and `test_a_dropped_namespace_placeholder_fails` and `test_a_dropped_skills_folder_rule_fails` and `test_a_dropped_degraded_state_fails` and `test_a_statement_without_a_derivation_note_fails` and `test_a_passing_prose_derivation_mention_fails` and `test_a_missing_decision_22_record_fails` and `test_a_decision_record_without_a_decision_4_statement_fails` in tests/test_antigravity.py |
| The canonical skill frontmatter four keys claim stood without a pin (R24-SP-02) | `test_a_dropped_four_keys_fails` in tests/test_antigravity.py |

The preserved lane R24-RT-04 vacuity guard limit and the
focus pins presence only limit (R24-RT-05) stand as
recorded guard limits with the spec lane diff review as
the guard for those shapes. The missing Build 11 bullet
repair (R24-ST-01) stands as prose. The per-sentence axis
claim (R24-SP-01) has no recorded closure in the round 24
fix report, so it stands here as an open record item. The
Build 13 citation upgrades handed forward to round 26
stand outside this section.

## Round 25 incidents

Round 25 was a research and plan refinement round and
raised no code incidents of its own. Its plan handed
the Build 13, Build 14, Build 15, and Build 16 builds
and the gate hardening rounds to rounds 26 through 29,
and the findings those rounds raised stand in their
own sections below. This section stands so the head of
this index can say that each round has its own section
and a reader can tell that round 25 was checked rather
than skipped.

## Round 26 incidents

| Incident | Covered by |
| --- | --- |
| A trusted head branch sentence passed the Copilot brief gate (R26-RT-01) | `test_a_trusted_head_branch_sentence_fails` and `test_a_reliable_head_branch_sentence_fails` and `test_a_head_branch_merge_authority_grant_fails` in tests/test_copilot.py |
| A named review model passed the Copilot brief gate (R26-RT-02) | `test_a_named_review_model_fails` in tests/test_copilot.py |
| A permitted approval on a red packet passed the Copilot brief gate (R26-RT-03) | `test_a_permitted_approval_on_a_red_packet_fails` and `test_a_reworded_approval_permission_fails` and `test_a_negated_approval_permission_passes` in tests/test_copilot.py |

The per sentence axis claim overstatement carried from
round 24 (R26-SP-01) closed in this round as brief
prose in the CodeRabbit brief and in decision 20, and
no test pins the axis wording by name. The en dash scan gap (R26-ST-01)
closed as a scan change in the copy gate, and the fence
tests in the gate script suite cover the dash family
without a dedicated en dash test name. The October 26
Copilot global default recheck was carried forward as
a watch item and stands outside this section.

## Round 27 incidents

| Incident | Covered by |
| --- | --- |
| A hook event without a blocking check and a notification only sentence passed the Kimi plugin gate (R27-RT-01) | `test_each_hook_event_carries_a_blocking_check` and `test_a_notification_only_sentence_fails` in tests/test_kimi.py |
| A plugin wins collision sentence passed the Kimi plugin gate (R27-RT-02) | `test_the_user_agent_wins_the_collision_fixture` and `test_a_plugin_wins_sentence_fails` in tests/test_kimi.py |
| A bare name sentence passed the Kimi plugin gate (R27-RT-03) | `test_a_bare_name_sentence_fails` and `test_a_bare_name_works_sentence_fails` in tests/test_kimi.py |
| A server start directory sentence passed the Kimi plugin gate (R27-RT-04) | `test_a_server_start_directory_sentence_fails` and `test_a_server_start_directory_noun_sentence_fails` in tests/test_kimi.py |
| An inflated size limit passed the Kimi plugin gate (R27-RT-05) | `test_an_inflated_limit_fails` and `test_an_inflated_limit_added_sentence_fails` in tests/test_kimi.py |
| A dropped print mode persona passed the Kimi plugin gate (R27-RT-06) | `test_a_dropped_persona_fails` and `test_a_persona_free_ci_sentence_fails` in tests/test_kimi.py |

The round 27 fix report on file is reconstructed by
the owner from the pushed commit record, and this
section carries that caveat with it. The spec and
standards items (R27-SP-01, R27-SP-02, R27-ST-01, and
R27-ST-02) closed inside the same build landing, and
the derivation note and dropped pin tests in
tests/test_kimi.py stand behind them without a one to
one name mapping in the reconstructed report.

## Round 28 incidents

| Incident | Covered by |
| --- | --- |
| A hook blocking rewording passed the Kimi plugin gate (R28-RT-01) | `test_a_replacement_hook_rewording_fails` and `test_a_failed_check_proceeds_sentence_fails` and `test_an_advisory_failure_sentence_fails` in tests/test_kimi.py |
| A collision precedence rewording passed the Kimi plugin gate (R28-RT-02) | `test_a_replacement_collision_rewording_fails` and `test_a_resolves_to_plugin_sentence_fails` and `test_a_plugin_precedence_sentence_fails` in tests/test_kimi.py |
| A qualified names rewording passed the Kimi plugin gate (R28-RT-03) | `test_a_replacement_qualified_rewording_fails` in tests/test_kimi.py |
| A server start directory rewording passed the Kimi plugin gate (R28-RT-04) | `test_a_replacement_workdir_rewording_fails` in tests/test_kimi.py |
| Five pinned claims stood with no negative of their own (R28-RT-05) | `test_a_swapped_fixture_pair_fails` and `test_dropped_secondary_sentences_fail` and `test_a_missing_numbering_note_fails` and `test_a_honoured_fields_sentence_fails` and `test_an_immediate_source_edit_sentence_fails` and `test_a_per_project_scope_sentence_fails` in tests/test_kimi.py |
| Derivation escapes and bare citation derivation notes passed the Kimi plugin gate (R28-RT-06 and R28-RT-07) | `test_an_unnumbered_rule_heading_fails` and `test_a_bare_paragraph_rule_fails` and `test_a_late_rule_section_fails` and `test_a_bare_kimi_citation_fails` and `test_a_bare_decision_citation_fails` in tests/test_kimi.py |
| A gutted decision record passed the Kimi plugin gate (R28-RT-09) | `test_a_gutted_decision_record_fails` in tests/test_kimi.py |
| Fixture contents stood unchecked and the live probe could fail open (R28-RT-10 and R28-RT-11) | `test_a_hostile_fixture_fails` and `test_an_always_blocking_fixture_fails_the_pass_probe` in tests/test_kimi.py |

The extractor flagging of the Kimi plugin surfaces
(R28-RT-08) stands in the extractor suite. Four
unpinned brief sentences (R28-RT-12) and the decision
21 gap (R28-RT-13) closed inside the same pin set the
rows above cite, with the unknown fields sentence of
R28-RT-12 shared with R28-SP-01. The external items
closed as brief corrections from primary pages, and
R28-EX-04 stands as an honest partial, with the
sandboxing half pinned primary in this round and the
Agent Framework stable half corroborated rather than
primary verified until round 29 closed it from the
vendor devblog.

## Round 29 incidents

| Incident | Covered by |
| --- | --- |
| Semantic negative groups stood missing across the Kimi plugin gate (R29-RT-06) | `test_a_no_form_autodiscovery_denial_fails` and `test_an_any_override_drop_fails` and `test_a_dropped_trust_workspace_pin_fails` and `test_a_dropped_unversioned_layout_pin_fails` and `test_a_noun_free_event_denial_fails` and `test_a_swapped_per_field_limit_fails` and `test_a_bare_name_subject_invocation_fails` in tests/test_kimi.py |
| A dropped version bump rule, a dropped register but not execute sentence, and a dropped description cap passed the ZCode plugin gate | `test_a_dropped_version_bump_sentence_fails` and `test_a_dropped_register_not_execute_sentence_fails` and `test_a_dropped_description_cap_fails` and `test_an_over_cap_description_fails` in tests/test_zcode.py |
| ZCode execution and cap restatements passed the ZCode plugin gate | `test_execution_and_cap_plants_fail` and `test_gate_review_execution_and_cap_restated_plants_fail` and `test_gate_review_other_host_cap_sentence_passes` in tests/test_zcode.py |
| Copilot trust and approval claims stood guarded by their rule position rather than their meaning | `test_trust_core_plants_after_the_rules_section_fail` and `test_gate_review_split_and_paraphrase_plants_fail` and `test_gate_review_negated_and_attributed_trust_passes` in tests/test_copilot.py |
| The live hook probe stood outside the gate function | `test_kimi_problems_includes_the_live_probe` and `test_a_live_all_events_fixture_fails_the_probe` in tests/test_kimi.py |

The remaining round 29 red team items closed across
the Kimi, ZCode, and Copilot gate hardening in this
round, including the kimi.plugin.json basename
flagging in all three extractor copies, and they stand
behind the negative groups the rows above cite without
a one to one name mapping in the fix report. The Build
15 omission from the round 28 report (R29-SP-01)
closed as decision 26, the dated deferral of Build 15
to round 33, and the round 33 section below records
its landing. The standards and external items closed
as pins and brief corrections in the same landing.

## Round 30 incidents

Round 30 was a research round and raised no code
incidents of its own. Its research record handed the
Build 13, Build 10, and Build 11 currency corrections
to round 31, and the findings that round raised stand
in their own section below. This section stands so the
head of this index can say that each round has its own
section and a reader can tell that round 30 was
checked rather than skipped.

## Round 31 incidents

| Incident | Covered by |
| --- | --- |
| A dropped Devin pin passed the Devin brief gate across the build surface | `test_a_dropped_bitbucket_host_fails` and `test_a_dropped_resolved_count_fails` and `test_a_dropped_sarif_pin_fails` and `test_a_dropped_v3beta1_continuation_fails` and `test_a_dropped_schedules_separation_fails` and `test_a_dropped_oncall_adjacent_fails` and `test_a_dropped_trigger_default_fails` and `test_a_dropped_stack_rule_fails` and `test_a_dropped_ai_scan_limit_fails` and `test_a_dropped_fusion_caveat_fails` in tests/test_devin.py |
| A bare Dynamic Workflows mention and a Build 6 figure about Devin passed the Devin brief gate | `test_a_bare_dynamic_workflows_mention_fails` and `test_a_build_6_figure_about_devin_fails` in tests/test_devin.py |
| A SARIF version swap and resolved count rewordings passed the Devin brief gate | `test_a_sarif_version_swap_fails` and `test_resolved_rewordings_fail` in tests/test_devin.py |
| Replacement rewordings of the Kimi claims passed the Kimi plugin gate | `test_a_replacement_hook_rewording_fails` and `test_a_replacement_collision_rewording_fails` and `test_a_replacement_qualified_rewording_fails` and `test_a_replacement_workdir_rewording_fails` and `test_a_replacement_secondary_rewording_fails` in tests/test_kimi.py |
| Synonym trust and approval sentences passed the Copilot brief gate | `test_a_synonym_trust_sentence_fails` and `test_a_synonym_approval_sentence_fails` in tests/test_copilot.py |

Two red team items closed as stated limitations
rather than new artifacts. R31-RT-12 stands as the
record that no version is invented where the primary
pages name none, and R31-RT-14 stands as the record
that no flipped task eval is claimed. The Build 13,
Build 10, and Build 11 currency corrections from the
round 30 record folded in this round as brief prose,
and the decision 25 phrasing wording narrowed to the
phrasing families the gate tests. The external items
closed as brief corrections from primary pages in the
same landing.

## Round 32 incidents

| Incident | Covered by |
| --- | --- |
| Devin contradictions in added, in rule, and replacement form passed the Devin brief gate (R32-RT-01) | `test_added_contradictions_fail` and `test_an_in_rule_resolved_contradiction_fails` and `test_replacement_contradictions_fail` in tests/test_devin.py |
| Copilot trust and approval stated with fresh synonyms passed the Copilot brief gate (R32-RT-02) | `test_r32_synonym_sentences_fail` in tests/test_copilot.py |
| Kimi precedence and bare name synonyms passed the Kimi plugin gate (R32-RT-04) | `test_r32_synonym_replacements_fail` in tests/test_kimi.py |

Decision 13 stands rewritten in this round to a
single condition suspended status with the dated Build
18 deferral, and no test pins the decision wording by
name. R32-EX-05 was carried forward as a guard rather
than closed by a tree change, and the round 34 section
below records its guard landing. R32-SP-05 closed by
locator rather than by dropping the sentence. No
finding in this round was declined on substance.

## Round 33 incidents

| Incident | Covered by |
| --- | --- |
| Qwen figure claims stood without their basis and scope (R33-RT-01, R33-RT-04, and R33-RT-08) | `test_every_plant_fails` and `test_the_number_normalisation_fires` and `test_a_dropped_figure_pin_fails` and `test_gate_review_split_figure_plants_fail` and `test_gate_review_unbound_figure_sentence_passes` in tests/test_qwen.py |
| The wrapper exits and the internal verify exit stood merged (R33-RT-02) | `test_a_dropped_wrapper_exit_fails` and `test_a_dropped_internal_verify_pin_fails` and `test_a_merged_exit_table_fails` in tests/test_qwen.py |
| A dropped activation, cancellation, precedence, or listing pin passed the Qwen brief gate (R33-RT-05 and R33-RT-06) | `test_a_dropped_not_activated_pin_fails` and `test_a_dropped_cancellation_pin_fails` and `test_a_dropped_precedence_pin_fails` and `test_a_dropped_no_listing_pin_fails` in tests/test_qwen.py |
| A dropped runtime unverified pin and a dropped derivation note passed the Qwen brief gate | `test_a_dropped_runtime_unverified_pin_fails` and `test_a_dropped_derivation_note_fails` and `test_a_dropped_r4_qoder_path_fails` and `test_a_dropped_qoder_activation_unverified_fails` in tests/test_qwen.py |
| A publication promise passed the Qwen brief gate | `test_a_publication_promise_fails` and `test_the_three_naming_cases` in tests/test_qwen.py |

The 12 against 16 figure conflict was not resolved to
a single figure in this round. The brief carries the
basis and scope table, and the gate forbids a bare
figure of either kind. Conversion fidelity holds for
the skill tree only, runtime invocation stays
UNVERIFIED, and the scoped npm route stays UNTESTED,
and those three records stand as open residuals beside
their pins. R33-SP-06 was carried forward as program
record and R33-EX-06 was carried forward as
UNVERIFIED. R33-RT-11 and R33-RT-12 closed by non
action, and the rechecks they name were carried
forward on their dates.

## Round 34 incidents

| Incident | Covered by |
| --- | --- |
| The corpus index stood behind the rounds it indexes | `test_a_renamed_cited_test_fails_the_corpus_check` and `test_a_corpus_name_that_never_existed_fails` and `test_a_dropped_corpus_row_fails_the_coverage_floor` and `test_a_dropped_corpus_citation_fails_the_coverage_floor` and `test_scope_cap_names_the_highest_round_section` in the gate script suite |
| Devin membership plants escaped through long filler between the verb and resolved | `test_verb_plus_membership_long_filler_fails` and `test_modifier_chain_membership_plants_fail` and `test_gate_review_degree_adverb_chain_plants_fail` and `test_gate_review_chain_true_sentences_pass` in tests/test_devin.py |
| Spelled SARIF versions passed the Devin brief gate | `test_spelled_sarif_versions_fail` in tests/test_devin.py |

The round then ran four repair layers over its own
gate. The G layer made the Qwen figure negative order
independent and sentence scoped with adverb
normalisation, and gave the wrapper, activation, and
alias negatives their missing synonyms and reversed
orders. The R layer normalised hyphens before matching
and bounded the Qwen reading. The Y layer and the B3
item tied the Devin membership phrases to resolved
within a measured bound, and one spec item in that
layer was a real regression, the beat pattern flagging
the true shipped precedence sentence in its active
form, repaired by restricting the pattern to the
passive form. The W and S layer closed the remaining
shapes of the same seams, and three confirmation lanes
approved the final delta. The single synonym residual
class stands accepted at the end of this round and is
not closed, and the escapes in it are single synonym
variants of families the gates already cover. R34-EX-01,
the scoped shape guard carried from round 32, landed
as a guard with no violation found in the set.

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
