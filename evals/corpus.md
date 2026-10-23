# Eval corpus from real failures

This index encodes the incidents the audit program actually
found, from the first cycle through round 1, and maps each one
to the regression test or fixture that now covers it. A test name in this file was checked against the suite in the same
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
records the deferral and its reason in the open.
