# Phase 1 observed test results

Updated 2026-10-27 (America/Indianapolis) after the approved test changes. NumPy 2.5.4; pytest 9.2.0; Python 3.12.14.

`.venv/Scripts/python -m pytest ai_record tests -v --tb=short --junitxml=tmp/phase1-full.xml`

**197 failed, 10 passed, 0 errors, 0 skipped; pytest exit code 1.** Plain `pytest` (tests only) gives 197 failed.

All failures are deliberate NotImplementedError stubs (checked from the JUnit XML). All passes belong to the existing AI-record suite. No numerical behavior is implemented or passing. Later assertions are not yet exercised: a clean collection does not prove every future assertion or algorithm is correct. Expected values in the new lecture and numerical tests were verified independently (see PHASE1.md and ai_record/decisions.md D014-D016), not by running a solver.

| Test group | Passed | Failed |
|---|---:|---:|
| ai_record.test_records.RecordTests | 10 | 0 |
| tests.test_interior | 0 | 24 |
| tests.test_lecture_examples | 0 | 31 |
| tests.test_model | 0 | 39 |
| tests.test_numerics | 0 | 35 |
| tests.test_results | 0 | 28 |
| tests.test_simplex | 0 | 40 |

The full verbose output and JUnit XML are local ignored files: tmp/phase1-full.txt and tmp/phase1-full.xml. This inventory is retained for review.

Assignment mapping and unresolved reference gaps: [PHASE1.md](PHASE1.md).

## Review corrections (Claude Code, after the original run)

- Bare `pytest` failed with 5 collection ImportErrors because `lp_solver` was not on the path; only `python -m pytest` worked. Added `pytest.ini` (`testpaths = tests`, `pythonpath = .`). Re-run: both `pytest` and `python -m pytest` give 152 failed, 0 errors.
- `assignment_size` fixtures used singleton rows (x_i <= 1), which are bounds in disguise and conflicted with the other eligibility tests. They now use distinct multi-variable rows.
- The empty-objective validation case also had a dimension mismatch, so it never isolated the empty objective. It now uses `c=[]` with a consistent empty `A`, `b`, `relations`.
- The rank-cutoff test relied on `1e-12*2*sigma_max == 2e-12` surviving an SVD in floating point. It now uses `diag([1, .5])` with `rank_tol=.25`, which is exact in binary.
- Cycling fixture label: I first renamed the test to say it was not Beale's 1955 example, from memory and without a source. Section 8 of the supplied lecture notes calls these exact coefficients the classical Beale example, so that claim is withdrawn. The test is now named for the course example (notes section 8) and asserts no attribution beyond the notes.
- Resolved after your review: the two `np.linalg` monkeypatch tests and the uncertain-rank solver test were replaced by implementation-independent tests (see decisions D016). They require no particular NumPy call and no particular status for borderline matrices; any returned optimum must pass an independent scale-aware KKT check.
- Pytest also emits 2 PytestCacheWarnings (`.pytest_cache` access denied on this machine); they are harmless and were not listed above.

## Complete observed inventory

| Test | Outcome | Observed reason |
|---|---|---|
| `ai_record.test_records.RecordTests::test_bundle_is_searchable_and_tampering_is_rejected` | PASS | Existing documentation behavior passed |
| `ai_record.test_records.RecordTests::test_bundle_refreshes_readable_copy_from_unchanged_raw_without_csv_dump` | PASS | Existing documentation behavior passed |
| `ai_record.test_records.RecordTests::test_continuation_replaces_session_and_rejects_shorter_history` | PASS | Existing documentation behavior passed |
| `ai_record.test_records.RecordTests::test_export_preserves_evidence_without_duplicate_messages_or_invented_reasoning` | PASS | Existing documentation behavior passed |
| `ai_record.test_records.RecordTests::test_invalid_source_fails_without_registering_it` | PASS | Existing documentation behavior passed |
| `ai_record.test_records.RecordTests::test_missing_attachment_is_marked_and_event_only_export_supported` | PASS | Existing documentation behavior passed |
| `ai_record.test_records.RecordTests::test_readable_export_keeps_prompts_replies_and_brief_source_notes` | PASS | Existing documentation behavior passed |
| `ai_record.test_records.RecordTests::test_supplied_document_is_named_without_exposing_runtime_preamble` | PASS | Existing documentation behavior passed |
| `ai_record.test_records.RecordTests::test_wait_final_captures_actual_saved_reply` | PASS | Existing documentation behavior passed |
| `ai_record.test_records.RecordTests::test_wait_final_timeout_does_not_invent_or_register_a_reply` | PASS | Existing documentation behavior passed |
| `tests.test_interior::test_primal_dual_residuals_objectives_and_average_complementarity` | FAIL | NotImplementedError: residuals: primal-dual diagnostics are pending |
| `tests.test_interior::test_newton_direction_satisfies_all_three_block_equations` | FAIL | NotImplementedError: newton_direction: centered Newton system is pending |
| `tests.test_interior::test_centering_target_is_sigma_times_average_not_affine_scaling` | FAIL | NotImplementedError: centered_target: complementarity target is pending |
| `tests.test_interior::test_fraction_to_boundary_is_capped_and_strictly_positive[v0-d0-0.495]` | FAIL | NotImplementedError: fraction_step: positivity-preserving step is pending |
| `tests.test_interior::test_fraction_to_boundary_is_capped_and_strictly_positive[v1-d1-1.0]` | FAIL | NotImplementedError: fraction_step: positivity-preserving step is pending |
| `tests.test_interior::test_fraction_to_boundary_is_capped_and_strictly_positive[v2-d2-1.0]` | FAIL | NotImplementedError: fraction_step: positivity-preserving step is pending |
| `tests.test_interior::test_fraction_to_boundary_is_capped_and_strictly_positive[v3-d3-0.495]` | FAIL | NotImplementedError: fraction_step: positivity-preserving step is pending |
| `tests.test_interior::test_interior_start_rejects_nonpositive_nonfinite_and_wrong_shapes[x0-y0-s0]` | FAIL | NotImplementedError: validate_start: interior initialization validation is pending |
| `tests.test_interior::test_interior_start_rejects_nonpositive_nonfinite_and_wrong_shapes[x1-y1-s1]` | FAIL | NotImplementedError: validate_start: interior initialization validation is pending |
| `tests.test_interior::test_interior_start_rejects_nonpositive_nonfinite_and_wrong_shapes[x2-y2-s2]` | FAIL | NotImplementedError: validate_start: interior initialization validation is pending |
| `tests.test_interior::test_interior_start_rejects_nonpositive_nonfinite_and_wrong_shapes[x3-y3-s3]` | FAIL | NotImplementedError: validate_start: interior initialization validation is pending |
| `tests.test_interior::test_interior_start_rejects_nonpositive_nonfinite_and_wrong_shapes[x4-y4-s4]` | FAIL | NotImplementedError: validate_start: interior initialization validation is pending |
| `tests.test_interior::test_interior_start_rejects_nonpositive_nonfinite_and_wrong_shapes[x5-y5-s5]` | FAIL | NotImplementedError: validate_start: interior initialization validation is pending |
| `tests.test_interior::test_interior_start_rejects_nonpositive_nonfinite_and_wrong_shapes[x6-y6-s6]` | FAIL | NotImplementedError: validate_start: interior initialization validation is pending |
| `tests.test_interior::test_interior_start_rejects_nonpositive_nonfinite_and_wrong_shapes[x7-y7-s7]` | FAIL | NotImplementedError: validate_start: interior initialization validation is pending |
| `tests.test_interior::test_interior_start_rejects_nonpositive_nonfinite_and_wrong_shapes[x8-y8-s8]` | FAIL | NotImplementedError: validate_start: interior initialization validation is pending |
| `tests.test_interior::test_infeasible_positive_start_needs_no_feasibility_solve` | FAIL | NotImplementedError: validate_start: interior initialization validation is pending |
| `tests.test_interior::test_rank_deficient_ip_input_is_unsupported_not_infeasible` | FAIL | NotImplementedError: solve: interior algorithm is deliberately unimplemented |
| `tests.test_interior::test_two_distinct_infeasible_starts_reach_same_known_optimum[start0]` | FAIL | NotImplementedError: solve: interior algorithm is deliberately unimplemented |
| `tests.test_interior::test_two_distinct_infeasible_starts_reach_same_known_optimum[start1]` | FAIL | NotImplementedError: solve: interior algorithm is deliberately unimplemented |
| `tests.test_interior::test_ip_logs_recompute_residuals_and_keep_every_iterate_interior` | FAIL | NotImplementedError: solve: interior algorithm is deliberately unimplemented |
| `tests.test_interior::test_first_centered_update_uses_separate_primal_and_dual_steps` | FAIL | NotImplementedError: solve: interior algorithm is deliberately unimplemented |
| `tests.test_interior::test_fixed_sigma_is_configurable_in_iteration_log` | FAIL | NotImplementedError: solve: interior algorithm is deliberately unimplemented |
| `tests.test_interior::test_newton_singular_system_raises_numerical_exception` | FAIL | NotImplementedError: newton_direction: centered Newton system is pending |
| `tests.test_lecture_examples::test_notes_basis_inverse_values_multipliers_and_reduced_costs[basis0-inverse0-x_b0-y0-reduced0]` | FAIL | NotImplementedError: basis_state: inverse and reduced-cost calculations are pending |
| `tests.test_lecture_examples::test_notes_basis_inverse_values_multipliers_and_reduced_costs[basis1-inverse1-x_b1-y1-reduced1]` | FAIL | NotImplementedError: basis_state: inverse and reduced-cost calculations are pending |
| `tests.test_lecture_examples::test_notes_basis_inverse_values_multipliers_and_reduced_costs[basis2-inverse2-x_b2-y2-reduced2]` | FAIL | NotImplementedError: basis_state: inverse and reduced-cost calculations are pending |
| `tests.test_lecture_examples::test_notes_basis_inverse_values_multipliers_and_reduced_costs[basis3-inverse3-x_b3-y3-reduced3]` | FAIL | NotImplementedError: basis_state: inverse and reduced-cost calculations are pending |
| `tests.test_lecture_examples::test_notes_bounded_example_optimum_and_certificate` | FAIL | NotImplementedError: solve: simplex algorithm is deliberately unimplemented |
| `tests.test_lecture_examples::test_notes_bounded_trace_under_bland` | FAIL | NotImplementedError: solve: simplex algorithm is deliberately unimplemented |
| `tests.test_lecture_examples::test_notes_unbounded_example_ray` | FAIL | NotImplementedError: solve: simplex algorithm is deliberately unimplemented |
| `tests.test_lecture_examples::test_notes_unbounded_region_with_bounded_objective` | FAIL | NotImplementedError: solve: simplex algorithm is deliberately unimplemented |
| `tests.test_lecture_examples::test_notes_degenerate_zero_length_pivot_reveals_certificate` | FAIL | NotImplementedError: solve: simplex algorithm is deliberately unimplemented |
| `tests.test_lecture_examples::test_notes_cycling_example_conversion_reproduces_standard_form` | FAIL | NotImplementedError: to_standard: general LP conversion is pending |
| `tests.test_lecture_examples::test_notes_cycling_example_bland_trace` | FAIL | NotImplementedError: solve: simplex algorithm is deliberately unimplemented |
| `tests.test_lecture_examples::test_notes_cycling_example_any_rule_must_still_reach_optimum_one` | FAIL | NotImplementedError: solve: simplex algorithm is deliberately unimplemented |
| `tests.test_lecture_examples::test_notes_leaving_choice_uses_variable_index_among_ratio_ties[values0-direction0-basis0-0-0]` | FAIL | NotImplementedError: bland_leave: ratio test and leaving variable selection are pending |
| `tests.test_lecture_examples::test_notes_leaving_choice_uses_variable_index_among_ratio_ties[values1-direction1-basis1-1-0]` | FAIL | NotImplementedError: bland_leave: ratio test and leaving variable selection are pending |
| `tests.test_lecture_examples::test_notes_leaving_choice_uses_variable_index_among_ratio_ties[values2-direction2-basis2-0-0]` | FAIL | NotImplementedError: bland_leave: ratio test and leaving variable selection are pending |
| `tests.test_lecture_examples::test_notes_leaving_choice_uses_variable_index_among_ratio_ties[values3-direction3-basis3-1-0]` | FAIL | NotImplementedError: bland_leave: ratio test and leaving variable selection are pending |
| `tests.test_lecture_examples::test_notes_leaving_choice_uses_variable_index_among_ratio_ties[values4-direction4-basis4-0-0]` | FAIL | NotImplementedError: bland_leave: ratio test and leaving variable selection are pending |
| `tests.test_lecture_examples::test_notes_leaving_choice_uses_variable_index_among_ratio_ties[values5-direction5-basis5-1-0]` | FAIL | NotImplementedError: bland_leave: ratio test and leaving variable selection are pending |
| `tests.test_lecture_examples::test_notes_leaving_choice_uses_variable_index_among_ratio_ties[values6-direction6-basis6-1-0]` | FAIL | NotImplementedError: bland_leave: ratio test and leaving variable selection are pending |
| `tests.test_lecture_examples::test_notes_bland_entering_prefers_smallest_index_over_most_negative` | FAIL | NotImplementedError: bland_enter: entering variable selection is pending |
| `tests.test_lecture_examples::test_good_identity_present_skips_phase_one` | FAIL | NotImplementedError: solve: simplex algorithm is deliberately unimplemented |
| `tests.test_lecture_examples::test_bad_conversion_matches_slides` | FAIL | NotImplementedError: to_standard: general LP conversion is pending |
| `tests.test_lecture_examples::test_bad_adds_artificials_only_to_rows_without_unit_columns` | FAIL | NotImplementedError: solve: simplex algorithm is deliberately unimplemented |
| `tests.test_lecture_examples::test_ugly_rank_is_deficient_not_infeasible` | FAIL | NotImplementedError: rank_diagnostics: scale-aware rank assessment is pending |
| `tests.test_lecture_examples::test_ugly_dependent_row_is_removed_with_evidence` | FAIL | NotImplementedError: solve: simplex algorithm is deliberately unimplemented |
| `tests.test_lecture_examples::test_ugly_inconsistent_rhs_is_infeasible` | FAIL | NotImplementedError: solve: simplex algorithm is deliberately unimplemented |
| `tests.test_lecture_examples::test_ugly_interior_rejects_dependent_rows_as_unsupported` | FAIL | NotImplementedError: solve: interior algorithm is deliberately unimplemented |
| `tests.test_lecture_examples::test_artificial_cleanup_removes_zero_artificial_in_dependent_row` | FAIL | NotImplementedError: remove_artificials: pivoting and redundant-row removal are pending |
| `tests.test_lecture_examples::test_dependent_rows_with_partial_identity_and_negative_rhs_variant` | FAIL | NotImplementedError: solve: simplex algorithm is deliberately unimplemented |
| `tests.test_lecture_examples::test_negative_rhs_surplus_reuse_starts_without_phase_one` | FAIL | NotImplementedError: solve: simplex algorithm is deliberately unimplemented |
| `tests.test_lecture_examples::test_negative_rhs_equality_needs_phase_one_and_solves` | FAIL | NotImplementedError: solve: simplex algorithm is deliberately unimplemented |
| `tests.test_model::test_reject_invalid_or_unsupported_input[changes0]` | FAIL | NotImplementedError: validate: LP validation is pending |
| `tests.test_model::test_reject_invalid_or_unsupported_input[changes1]` | FAIL | NotImplementedError: validate: LP validation is pending |
| `tests.test_model::test_reject_invalid_or_unsupported_input[changes2]` | FAIL | NotImplementedError: validate: LP validation is pending |
| `tests.test_model::test_reject_invalid_or_unsupported_input[changes3]` | FAIL | NotImplementedError: validate: LP validation is pending |
| `tests.test_model::test_reject_invalid_or_unsupported_input[changes4]` | FAIL | NotImplementedError: validate: LP validation is pending |
| `tests.test_model::test_reject_invalid_or_unsupported_input[changes5]` | FAIL | NotImplementedError: validate: LP validation is pending |
| `tests.test_model::test_reject_invalid_or_unsupported_input[changes6]` | FAIL | NotImplementedError: validate: LP validation is pending |
| `tests.test_model::test_reject_invalid_or_unsupported_input[changes7]` | FAIL | NotImplementedError: validate: LP validation is pending |
| `tests.test_model::test_reject_invalid_or_unsupported_input[changes8]` | FAIL | NotImplementedError: validate: LP validation is pending |
| `tests.test_model::test_reject_invalid_or_unsupported_input[changes9]` | FAIL | NotImplementedError: validate: LP validation is pending |
| `tests.test_model::test_reject_invalid_or_unsupported_input[changes10]` | FAIL | NotImplementedError: validate: LP validation is pending |
| `tests.test_model::test_reject_invalid_or_unsupported_input[changes11]` | FAIL | NotImplementedError: validate: LP validation is pending |
| `tests.test_model::test_reject_invalid_or_unsupported_input[changes12]` | FAIL | NotImplementedError: validate: LP validation is pending |
| `tests.test_model::test_reject_invalid_or_unsupported_input[changes13]` | FAIL | NotImplementedError: validate: LP validation is pending |
| `tests.test_model::test_reject_invalid_or_unsupported_input[changes14]` | FAIL | NotImplementedError: validate: LP validation is pending |
| `tests.test_model::test_reject_invalid_or_unsupported_input[changes15]` | FAIL | NotImplementedError: validate: LP validation is pending |
| `tests.test_model::test_reject_invalid_or_unsupported_input[changes16]` | FAIL | NotImplementedError: validate: LP validation is pending |
| `tests.test_model::test_reject_invalid_or_unsupported_input[changes17]` | FAIL | NotImplementedError: validate: LP validation is pending |
| `tests.test_model::test_reject_invalid_or_unsupported_input[changes18]` | FAIL | NotImplementedError: validate: LP validation is pending |
| `tests.test_model::test_reject_invalid_or_unsupported_input[changes19]` | FAIL | NotImplementedError: validate: LP validation is pending |
| `tests.test_model::test_validation_accepts_small_continuous_lp_and_does_not_mutate` | FAIL | NotImplementedError: validate: LP validation is pending |
| `tests.test_model::test_max_mixed_rows_negative_rhs_and_objective_recovery` | FAIL | NotImplementedError: to_standard: general LP conversion is pending |
| `tests.test_model::test_bound_substitution_and_objective_offset[bound0-3-z0-original0-15]` | FAIL | NotImplementedError: to_standard: general LP conversion is pending |
| `tests.test_model::test_bound_substitution_and_objective_offset[bound1-3-z1-original1-3]` | FAIL | NotImplementedError: to_standard: general LP conversion is pending |
| `tests.test_model::test_bound_substitution_and_objective_offset[bound2-3-z2-original2--9]` | FAIL | NotImplementedError: to_standard: general LP conversion is pending |
| `tests.test_model::test_bound_substitution_and_objective_offset[bound3-3-z3-original3-6]` | FAIL | NotImplementedError: to_standard: general LP conversion is pending |
| `tests.test_model::test_finite_interval_adds_upper_bound_row` | FAIL | NotImplementedError: to_standard: general LP conversion is pending |
| `tests.test_model::test_max_offset_and_shifted_constraint_rhs` | FAIL | NotImplementedError: to_standard: general LP conversion is pending |
| `tests.test_model::test_default_nonnegative_and_empty_rows_preserve_dimension` | FAIL | NotImplementedError: to_standard: general LP conversion is pending |
| `tests.test_model::test_assignment_size_uses_original_model[8-5-True]` | FAIL | NotImplementedError: assignment_size: original-model eligibility check is pending |
| `tests.test_model::test_assignment_size_uses_original_model[7-5-False]` | FAIL | NotImplementedError: assignment_size: original-model eligibility check is pending |
| `tests.test_model::test_assignment_size_uses_original_model[8-4-False]` | FAIL | NotImplementedError: assignment_size: original-model eligibility check is pending |
| `tests.test_model::test_nonnegative_declarations_and_generated_rows_do_not_meet_assignment_size` | FAIL | NotImplementedError: assignment_size: original-model eligibility check is pending |
| `tests.test_model::test_nonnegative_rows_are_not_substantive_assignment_constraints` | FAIL | NotImplementedError: assignment_size: original-model eligibility check is pending |
| `tests.test_model::test_unknown_solver_rejected_instead_of_silent_fallback` | FAIL | NotImplementedError: solve: typo algorithm is deliberately unimplemented |
| `tests.test_model::test_conversion_does_not_mutate_numpy_inputs` | FAIL | NotImplementedError: to_standard: general LP conversion is pending |
| `tests.test_model::test_greater_equal_surplus_is_negative` | FAIL | NotImplementedError: to_standard: general LP conversion is pending |
| `tests.test_model::test_free_variable_reconstruction_is_many_to_one` | FAIL | NotImplementedError: to_standard: general LP conversion is pending |
| `tests.test_model::test_recovery_rejects_wrong_standard_dimension` | FAIL | NotImplementedError: to_standard: general LP conversion is pending |
| `tests.test_numerics::test_raw_and_normalized_diagnostics_use_documented_denominators` | FAIL | NotImplementedError: residuals: primal-dual diagnostics are pending |
| `tests.test_numerics::test_feasible_positive_start_is_accepted_by_general_api` | FAIL | NotImplementedError: validate_start: interior initialization validation is pending |
| `tests.test_numerics::test_exact_kkt_point_satisfies_stopping_checks` | FAIL | NotImplementedError: converged: joint stopping criteria are pending |
| `tests.test_numerics::test_small_mu_alone_or_nonfinite_data_never_establishes_optimality[x0-y0-s0]` | FAIL | NotImplementedError: converged: joint stopping criteria are pending |
| `tests.test_numerics::test_small_mu_alone_or_nonfinite_data_never_establishes_optimality[x1-y1-s1]` | FAIL | NotImplementedError: converged: joint stopping criteria are pending |
| `tests.test_numerics::test_small_mu_alone_or_nonfinite_data_never_establishes_optimality[x2-y2-s2]` | FAIL | NotImplementedError: converged: joint stopping criteria are pending |
| `tests.test_numerics::test_small_mu_alone_or_nonfinite_data_never_establishes_optimality[x3-y3-s3]` | FAIL | NotImplementedError: converged: joint stopping criteria are pending |
| `tests.test_numerics::test_small_mu_alone_or_nonfinite_data_never_establishes_optimality[x4-y4-s4]` | FAIL | NotImplementedError: converged: joint stopping criteria are pending |
| `tests.test_numerics::test_normalized_gap_is_independent_guard_beyond_average_complementarity` | FAIL | NotImplementedError: converged: joint stopping criteria are pending |
| `tests.test_numerics::test_normalized_mu_is_checked_even_if_gap_tolerance_is_met` | FAIL | NotImplementedError: converged: joint stopping criteria are pending |
| `tests.test_numerics::test_large_objectives_cannot_hide_large_primal_residual` | FAIL | NotImplementedError: converged: joint stopping criteria are pending |
| `tests.test_numerics::test_tolerance_is_configurable_and_boundary_is_inclusive` | FAIL | NotImplementedError: converged: joint stopping criteria are pending |
| `tests.test_numerics::test_zero_residuals_and_gap_do_not_excuse_negative_primal_variables` | FAIL | NotImplementedError: converged: joint stopping criteria are pending |
| `tests.test_numerics::test_zero_residuals_and_gap_do_not_excuse_negative_dual_slacks` | FAIL | NotImplementedError: converged: joint stopping criteria are pending |
| `tests.test_numerics::test_solver_stopping_rejects_negative_basic_value_with_zero_complementarity` | FAIL | NotImplementedError: converged: joint stopping criteria are pending |
| `tests.test_numerics::test_nonnegativity_tolerance_is_explicit_and_configurable` | FAIL | NotImplementedError: converged: joint stopping criteria are pending |
| `tests.test_numerics::test_invalid_numerical_options_are_input_errors[change0]` | FAIL | NotImplementedError: validate_options: numerical policy validation is pending |
| `tests.test_numerics::test_invalid_numerical_options_are_input_errors[change1]` | FAIL | NotImplementedError: validate_options: numerical policy validation is pending |
| `tests.test_numerics::test_invalid_numerical_options_are_input_errors[change2]` | FAIL | NotImplementedError: validate_options: numerical policy validation is pending |
| `tests.test_numerics::test_invalid_numerical_options_are_input_errors[change3]` | FAIL | NotImplementedError: validate_options: numerical policy validation is pending |
| `tests.test_numerics::test_invalid_numerical_options_are_input_errors[change4]` | FAIL | NotImplementedError: validate_options: numerical policy validation is pending |
| `tests.test_numerics::test_invalid_numerical_options_are_input_errors[change5]` | FAIL | NotImplementedError: validate_options: numerical policy validation is pending |
| `tests.test_numerics::test_invalid_numerical_options_are_input_errors[change6]` | FAIL | NotImplementedError: validate_options: numerical policy validation is pending |
| `tests.test_numerics::test_invalid_numerical_options_are_input_errors[change7]` | FAIL | NotImplementedError: validate_options: numerical policy validation is pending |
| `tests.test_numerics::test_invalid_numerical_options_are_input_errors[change8]` | FAIL | NotImplementedError: validate_options: numerical policy validation is pending |
| `tests.test_numerics::test_invalid_numerical_options_are_input_errors[change9]` | FAIL | NotImplementedError: validate_options: numerical policy validation is pending |
| `tests.test_numerics::test_invalid_numerical_options_are_input_errors[change10]` | FAIL | NotImplementedError: validate_options: numerical policy validation is pending |
| `tests.test_numerics::test_invalid_numerical_options_are_input_errors[change11]` | FAIL | NotImplementedError: validate_options: numerical policy validation is pending |
| `tests.test_numerics::test_invalid_numerical_options_are_input_errors[change12]` | FAIL | NotImplementedError: validate_options: numerical policy validation is pending |
| `tests.test_numerics::test_valid_configurable_options_are_accepted` | FAIL | NotImplementedError: validate_options: numerical policy validation is pending |
| `tests.test_numerics::test_rank_assessment_is_invariant_under_uniform_scaling[1e-20]` | FAIL | NotImplementedError: rank_diagnostics: scale-aware rank assessment is pending |
| `tests.test_numerics::test_rank_assessment_is_invariant_under_uniform_scaling[1.0]` | FAIL | NotImplementedError: rank_diagnostics: scale-aware rank assessment is pending |
| `tests.test_numerics::test_rank_assessment_is_invariant_under_uniform_scaling[1e+20]` | FAIL | NotImplementedError: rank_diagnostics: scale-aware rank assessment is pending |
| `tests.test_numerics::test_exact_dependent_rows_report_rank_deficiency_not_infeasibility` | FAIL | NotImplementedError: rank_diagnostics: scale-aware rank assessment is pending |
| `tests.test_numerics::test_rank_at_cutoff_is_uncertain_not_a_proof_of_infeasibility` | FAIL | NotImplementedError: rank_diagnostics: scale-aware rank assessment is pending |
| `tests.test_results::test_zero_iteration_budget_is_limit_never_infeasible_or_optimal[simplex]` | FAIL | NotImplementedError: solve: simplex algorithm is deliberately unimplemented |
| `tests.test_results::test_zero_iteration_budget_is_limit_never_infeasible_or_optimal[interior]` | FAIL | NotImplementedError: solve: interior algorithm is deliberately unimplemented |
| `tests.test_results::test_simplex_trace_contains_both_phases_and_mathematically_consistent_basis` | FAIL | NotImplementedError: solve: simplex algorithm is deliberately unimplemented |
| `tests.test_results::test_optimal_standard_certificate_checks_primal_dual_gap_and_slacks[simplex]` | FAIL | NotImplementedError: solve: simplex algorithm is deliberately unimplemented |
| `tests.test_results::test_optimal_standard_certificate_checks_primal_dual_gap_and_slacks[interior]` | FAIL | NotImplementedError: solve: interior algorithm is deliberately unimplemented |
| `tests.test_results::test_certificate_checker_rejects_corrupted_claim[primal]` | FAIL | NotImplementedError: check_certificate: independent certificate checks are pending |
| `tests.test_results::test_certificate_checker_rejects_corrupted_claim[dual]` | FAIL | NotImplementedError: check_certificate: independent certificate checks are pending |
| `tests.test_results::test_certificate_checker_rejects_corrupted_claim[objective]` | FAIL | NotImplementedError: check_certificate: independent certificate checks are pending |
| `tests.test_results::test_certificate_checker_rejects_corrupted_claim[nan]` | FAIL | NotImplementedError: check_certificate: independent certificate checks are pending |
| `tests.test_results::test_original_max_solution_and_objective_survive_conversion[simplex]` | FAIL | NotImplementedError: solve: simplex algorithm is deliberately unimplemented |
| `tests.test_results::test_original_max_solution_and_objective_survive_conversion[interior]` | FAIL | NotImplementedError: solve: interior algorithm is deliberately unimplemented |
| `tests.test_results::test_positive_constraint_scaling_keeps_known_solution[simplex]` | FAIL | NotImplementedError: solve: simplex algorithm is deliberately unimplemented |
| `tests.test_results::test_positive_constraint_scaling_keeps_known_solution[interior]` | FAIL | NotImplementedError: solve: interior algorithm is deliberately unimplemented |
| `tests.test_results::test_certificate_checker_accepts_literal_valid_optimal_certificate` | FAIL | NotImplementedError: check_certificate: independent certificate checks are pending |
| `tests.test_results::test_certificate_checker_accepts_literal_ray_and_rejects_nonimproving_ray` | FAIL | NotImplementedError: check_certificate: independent certificate checks are pending |
| `tests.test_results::test_optimal_certificate_cannot_omit_nonnegativity_check` | FAIL | NotImplementedError: check_certificate: independent certificate checks are pending |
| `tests.test_results::test_hard_inputs_never_fake_success[tiny_pivot-simplex]` | FAIL | NotImplementedError: solve: simplex algorithm is deliberately unimplemented |
| `tests.test_results::test_hard_inputs_never_fake_success[tiny_pivot-interior]` | FAIL | NotImplementedError: solve: interior algorithm is deliberately unimplemented |
| `tests.test_results::test_hard_inputs_never_fake_success[huge_scale-simplex]` | FAIL | NotImplementedError: solve: simplex algorithm is deliberately unimplemented |
| `tests.test_results::test_hard_inputs_never_fake_success[huge_scale-interior]` | FAIL | NotImplementedError: solve: interior algorithm is deliberately unimplemented |
| `tests.test_results::test_hard_inputs_never_fake_success[tiny_scale-simplex]` | FAIL | NotImplementedError: solve: simplex algorithm is deliberately unimplemented |
| `tests.test_results::test_hard_inputs_never_fake_success[tiny_scale-interior]` | FAIL | NotImplementedError: solve: interior algorithm is deliberately unimplemented |
| `tests.test_results::test_hard_inputs_never_fake_success[near_dependent-simplex]` | FAIL | NotImplementedError: solve: simplex algorithm is deliberately unimplemented |
| `tests.test_results::test_hard_inputs_never_fake_success[near_dependent-interior]` | FAIL | NotImplementedError: solve: interior algorithm is deliberately unimplemented |
| `tests.test_results::test_nearly_dependent_but_feasible_never_reports_infeasible[simplex]` | FAIL | NotImplementedError: solve: simplex algorithm is deliberately unimplemented |
| `tests.test_results::test_nearly_dependent_but_feasible_never_reports_infeasible[interior]` | FAIL | NotImplementedError: solve: interior algorithm is deliberately unimplemented |
| `tests.test_results::test_nearly_dependent_infeasible_is_never_optimal[simplex-allowed0]` | FAIL | NotImplementedError: solve: simplex algorithm is deliberately unimplemented |
| `tests.test_results::test_nearly_dependent_infeasible_is_never_optimal[interior-allowed1]` | FAIL | NotImplementedError: solve: interior algorithm is deliberately unimplemented |
| `tests.test_simplex::test_basis_inverse_basic_values_dual_and_reduced_costs` | FAIL | NotImplementedError: basis_state: inverse and reduced-cost calculations are pending |
| `tests.test_simplex::test_bland_enter_uses_smallest_eligible_original_index` | FAIL | NotImplementedError: bland_enter: entering variable selection is pending |
| `tests.test_simplex::test_bland_enter_excludes_negligible_negative_costs` | FAIL | NotImplementedError: bland_enter: entering variable selection is pending |
| `tests.test_simplex::test_bland_leave_tie_uses_variable_index_not_row` | FAIL | NotImplementedError: bland_leave: ratio test and leaving variable selection are pending |
| `tests.test_simplex::test_ratio_test_ignores_nonpositive_direction_and_keeps_zero_step` | FAIL | NotImplementedError: bland_leave: ratio test and leaving variable selection are pending |
| `tests.test_simplex::test_no_eligible_ratio_signals_unbounded_direction` | FAIL | NotImplementedError: bland_leave: ratio test and leaving variable selection are pending |
| `tests.test_simplex::test_combined_absolute_relative_ratio_ties[values0-1]` | FAIL | NotImplementedError: bland_leave: ratio test and leaving variable selection are pending |
| `tests.test_simplex::test_combined_absolute_relative_ratio_ties[values1-1]` | FAIL | NotImplementedError: bland_leave: ratio test and leaving variable selection are pending |
| `tests.test_simplex::test_combined_absolute_relative_ratio_ties[values2-0]` | FAIL | NotImplementedError: bland_leave: ratio test and leaving variable selection are pending |
| `tests.test_simplex::test_smaller_bland_index_cannot_override_basic_nonnegativity` | FAIL | NotImplementedError: bland_leave: ratio test and leaving variable selection are pending |
| `tests.test_simplex::test_tiny_positive_pivot_cannot_falsely_certify_unboundedness` | FAIL | NotImplementedError: solve: simplex algorithm is deliberately unimplemented |
| `tests.test_simplex::test_phase_one_flips_negative_rhs_and_builds_identity_artificials` | FAIL | NotImplementedError: phase_one: artificial-basis construction is pending |
| `tests.test_simplex::test_phase_one_reuses_feasible_unit_columns_and_adds_only_needed_artificials[A0-b0-eA0-eb0-ec0-basis0-artificial0]` | FAIL | NotImplementedError: phase_one: artificial-basis construction is pending |
| `tests.test_simplex::test_phase_one_reuses_feasible_unit_columns_and_adds_only_needed_artificials[A1-b1-eA1-eb1-ec1-basis1-artificial1]` | FAIL | NotImplementedError: phase_one: artificial-basis construction is pending |
| `tests.test_simplex::test_phase_one_reuses_feasible_unit_columns_and_adds_only_needed_artificials[A2-b2-eA2-eb2-ec2-basis2-artificial2]` | FAIL | NotImplementedError: phase_one: artificial-basis construction is pending |
| `tests.test_simplex::test_phase_one_reuses_feasible_unit_columns_and_adds_only_needed_artificials[A3-b3-eA3-eb3-ec3-basis3-artificial3]` | FAIL | NotImplementedError: phase_one: artificial-basis construction is pending |
| `tests.test_simplex::test_phase_one_reuses_feasible_unit_columns_and_adds_only_needed_artificials[A4-b4-eA4-eb4-ec4-basis4-artificial4]` | FAIL | NotImplementedError: phase_one: artificial-basis construction is pending |
| `tests.test_simplex::test_phase_one_reuses_feasible_unit_columns_and_adds_only_needed_artificials[A5-b5-eA5-eb5-ec5-basis5-artificial5]` | FAIL | NotImplementedError: phase_one: artificial-basis construction is pending |
| `tests.test_simplex::test_phase_one_reuses_feasible_unit_columns_and_adds_only_needed_artificials[A6-b6-eA6-eb6-ec6-basis6-artificial6]` | FAIL | NotImplementedError: phase_one: artificial-basis construction is pending |
| `tests.test_simplex::test_phase_one_reuses_feasible_unit_columns_and_adds_only_needed_artificials[A7-b7-eA7-eb7-ec7-basis7-artificial7]` | FAIL | NotImplementedError: phase_one: artificial-basis construction is pending |
| `tests.test_simplex::test_zero_basic_artificial_is_pivoted_out` | FAIL | NotImplementedError: remove_artificials: pivoting and redundant-row removal are pending |
| `tests.test_simplex::test_redundancy_checks_augmented_rhs_not_only_matrix_rank` | FAIL | NotImplementedError: solve: simplex algorithm is deliberately unimplemented |
| `tests.test_simplex::test_finite_optima_including_degeneracy_dependency_and_empty_rows[p0-x0--10]` | FAIL | NotImplementedError: solve: simplex algorithm is deliberately unimplemented |
| `tests.test_simplex::test_finite_optima_including_degeneracy_dependency_and_empty_rows[p1-x1-1]` | FAIL | NotImplementedError: solve: simplex algorithm is deliberately unimplemented |
| `tests.test_simplex::test_finite_optima_including_degeneracy_dependency_and_empty_rows[p2-None--1]` | FAIL | NotImplementedError: solve: simplex algorithm is deliberately unimplemented |
| `tests.test_simplex::test_finite_optima_including_degeneracy_dependency_and_empty_rows[p3-x3-0]` | FAIL | NotImplementedError: solve: simplex algorithm is deliberately unimplemented |
| `tests.test_simplex::test_finite_optima_including_degeneracy_dependency_and_empty_rows[p4-x4-0]` | FAIL | NotImplementedError: solve: simplex algorithm is deliberately unimplemented |
| `tests.test_simplex::test_phase_one_positive_sum_certifies_infeasibility` | FAIL | NotImplementedError: solve: simplex algorithm is deliberately unimplemented |
| `tests.test_simplex::test_unbounded_feasible_point_and_improving_ray` | FAIL | NotImplementedError: solve: simplex algorithm is deliberately unimplemented |
| `tests.test_simplex::test_blands_rule_escapes_course_cycling_example` | FAIL | NotImplementedError: solve: simplex algorithm is deliberately unimplemented |
| `tests.test_simplex::test_singular_basis_is_explicit_numerical_exception` | FAIL | NotImplementedError: basis_state: inverse and reduced-cost calculations are pending |
| `tests.test_simplex::test_removed_row_evidence_preserves_augmented_dependence` | FAIL | NotImplementedError: solve: simplex algorithm is deliberately unimplemented |
| `tests.test_simplex::test_zero_row_with_nonzero_rhs_is_infeasible` | FAIL | NotImplementedError: solve: simplex algorithm is deliberately unimplemented |
| `tests.test_simplex::test_zero_redundant_equality_does_not_block_optimum` | FAIL | NotImplementedError: solve: simplex algorithm is deliberately unimplemented |
| `tests.test_simplex::test_unconstrained_improving_nonnegative_variable_is_unbounded` | FAIL | NotImplementedError: solve: simplex algorithm is deliberately unimplemented |
| `tests.test_simplex::test_alternate_optimum_has_zero_nonbasic_reduced_cost` | FAIL | NotImplementedError: solve: simplex algorithm is deliberately unimplemented |
| `tests.test_simplex::test_bad_basis_duplicate_indices_is_input_error` | FAIL | NotImplementedError: basis_state: inverse and reduced-cost calculations are pending |
| `tests.test_simplex::test_basis_inverse_is_recomputed_when_matrix_changes` | FAIL | NotImplementedError: basis_state: inverse and reduced-cost calculations are pending |
| `tests.test_simplex::test_all_zero_redundant_row_is_removed_with_artificial_column` | FAIL | NotImplementedError: remove_artificials: pivoting and redundant-row removal are pending |
| `tests.test_simplex::test_phase_one_known_positive_optimum_is_one` | FAIL | NotImplementedError: solve: simplex algorithm is deliberately unimplemented |
