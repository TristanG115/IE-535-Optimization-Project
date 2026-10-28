"""Literal small examples; none claimed to come from missing lecture notes."""
import numpy as np
import pytest
from numpy.testing import assert_allclose
from lp_solver import (LP, Options, solve, basis_state, bland_enter,
                       bland_leave, phase_one, remove_artificials)


def test_basis_inverse_basic_values_dual_and_reduced_costs():
    # B=[[1,1],[0,1]], B^-1=[[1,-1],[0,1]]; c_B=(-3,-2).
    state = basis_state(np.array([[1., 1, 1, 0], [0, 1, 0, 1]]),
                        np.array([4., 2]), np.array([-3., -2, 0, 0]), [0, 1])
    assert_allclose(state.inverse, [[1, -1], [0, 1]])
    assert_allclose(state.basic_values, [2, 2])
    assert_allclose(state.y, [-3, 1])
    assert_allclose(state.reduced_costs, [0, 0, 3, -1])


def test_bland_enter_uses_smallest_eligible_original_index():
    assert bland_enter(np.array([-10., -1, 0]), [7, 2, 9], tolerance=1e-9) == 2


def test_bland_enter_excludes_negligible_negative_costs():
    assert bland_enter(np.array([-1e-12, 0.]), [0, 1], tolerance=1e-9) is None


def test_bland_leave_tie_uses_variable_index_not_row():
    row, step = bland_leave(np.array([2., 1]), np.array([2., 1]), [8, 3],
                            pivot_tol=1e-12, tie_atol=1e-10, tie_rtol=1e-9, feas_tol=1e-8)
    assert row == 1
    assert step == pytest.approx(1)


def test_ratio_test_ignores_nonpositive_direction_and_keeps_zero_step():
    row, step = bland_leave(np.array([4., 0, 2]), np.array([-1., 2, 0]), [0, 7, 4],
                            pivot_tol=1e-12, tie_atol=1e-10, tie_rtol=1e-9, feas_tol=1e-8)
    assert (row, step) == (1, 0)


def test_no_eligible_ratio_signals_unbounded_direction():
    assert bland_leave(np.array([1., 2]), np.array([0., -1]), [0, 1],
                       pivot_tol=1e-12, tie_atol=1e-10, tie_rtol=1e-9, feas_tol=1e-8) == (None, None)


@pytest.mark.parametrize('values,expected_row', [
    ([1., 1. + 5e-11], 1),  # absolute tie, smaller ID may leave
    ([1e9, 1e9 + .5], 1),   # relative tie at large scale
    ([1., 1.01], 0),        # genuinely different ratios are not Bland ties
])
def test_combined_absolute_relative_ratio_ties(values, expected_row):
    values = np.array(values)
    row, step = bland_leave(values, np.ones(2), [8, 3], pivot_tol=1e-12,
                            tie_atol=1e-10, tie_rtol=1e-9, feas_tol=1e-8)
    assert row == expected_row
    assert step == pytest.approx(values[expected_row], rel=1e-12, abs=1e-12)
    assert min(values-step) >= -1e-8*(1+max(abs(values)))


def test_smaller_bland_index_cannot_override_basic_nonnegativity():
    values = np.array([1., 1.+5e-10])
    row, step = bland_leave(values, np.ones(2), [8, 3], pivot_tol=1e-12,
                            tie_atol=1e-10, tie_rtol=1e-9, feas_tol=1e-12)
    # Row 1 is a ratio tie with smaller ID, but its own step makes row 0
    # negative by 5e-10, exceeding the ~2e-12 feasibility allowance.
    assert row == 0
    assert step == pytest.approx(1., abs=1e-14)
    assert np.min(values-step) >= -1e-12*(1+max(abs(values)))


def test_tiny_positive_pivot_cannot_falsely_certify_unboundedness():
    result = solve(LP([-1], [[1e-14]], [1], ['<=']), method='simplex')
    assert result.status in {'optimal', 'numerical_failure'}
    if result.status == 'optimal':
        assert result.x[0] == pytest.approx(1e14, rel=1e-8)
    else:
        assert result.message


def test_phase_one_flips_negative_rhs_and_builds_identity_artificials():
    state = phase_one(np.array([[-1., 2], [2, 1]]), np.array([-3., 4]))
    assert_allclose(state.A, [[1, -2, 1, 0], [2, 1, 0, 1]])
    assert_allclose(state.b, [3, 4])
    assert_allclose(state.c, [0, 0, 1, 1])
    assert state.basis == [2, 3]
    assert state.artificial == [2, 3]


@pytest.mark.parametrize('A,b,eA,eb,ec,basis,artificial', [
    # Negative RHS: flipping makes the surplus column +e1, a feasible start; no artificial.
    ([[1., 2, -1]], [-4.], [[-1, -2, 1]], [4], [0, 0, 0], [2], []),
    # Negative RHS trap: +1 before the flip is -1 after it, so it cannot be reused.
    ([[1., 1]], [-1.], [[-1, -1, 1]], [1], [0, 0, 1], [2], [2]),
    # Duplicate unit columns: the largest index is used (slacks follow structural columns).
    ([[1., 1]], [2.], [[1, 1]], [2], [0, 0], [1], []),
    # A zero RHS is a valid (degenerate) feasible basic value.
    ([[1., 1]], [0.], [[1, 1]], [0], [0, 0], [1], []),
    # Slides, The Good: I_2 is columns 3-4, so Phase I is not needed.
    ([[1., 1, 1, 0], [-1, 2, 0, 1]], [4., 2], [[1, 1, 1, 0], [-1, 2, 0, 1]], [4, 2],
     [0, 0, 0, 0], [2, 3], []),
    # Slides, The Bad: only e3 is present; artificials go on rows 1 and 2 only.
    ([[1., 1, -1, 0], [1, 2, 0, 0], [2, 1, 0, 1]], [2., 3, 6],
     [[1, 1, -1, 0, 1, 0], [1, 2, 0, 0, 0, 1], [2, 1, 0, 1, 0, 0]], [2, 3, 6],
     [0, 0, 0, 0, 1, 1], [4, 5, 3], [4, 5]),
    # Slides, The Ugly: no unit columns, three artificials (row3 = row1 + row2).
    ([[1., 1, 1], [1, 2, 3], [2, 3, 4]], [4., 7, 11],
     [[1, 1, 1, 1, 0, 0], [1, 2, 3, 0, 1, 0], [2, 3, 4, 0, 0, 1]], [4, 7, 11],
     [0, 0, 0, 1, 1, 1], [3, 4, 5], [3, 4, 5]),
    # Dependent rows 1 and 2 (row2 = 2*row1) with e3 present: artificials on rows 1-2 only.
    ([[1., 1, 0], [2, 2, 0], [0, 0, 1]], [1., 2, 3],
     [[1, 1, 0, 1, 0], [2, 2, 0, 0, 1], [0, 0, 1, 0, 0]], [1, 2, 3],
     [0, 0, 0, 1, 1], [3, 4, 2], [3, 4]),
])
def test_phase_one_reuses_feasible_unit_columns_and_adds_only_needed_artificials(
        A, b, eA, eb, ec, basis, artificial):
    A, b = np.array(A), np.array(b)
    A0, b0 = A.copy(), b.copy()
    state = phase_one(A, b)
    assert_allclose(state.A, eA)
    assert_allclose(state.b, eb)
    assert_allclose(state.c, ec)
    assert state.basis == basis
    assert state.artificial == artificial
    assert_allclose(A, A0)  # inputs are not mutated
    assert_allclose(b, b0)
    assert np.min(state.b) >= 0
    assert_allclose(state.A[:, state.basis], np.eye(len(b)))  # identity basis


def test_zero_basic_artificial_is_pivoted_out():
    state = remove_artificials(np.array([[1., 1]]), np.array([0.]), [1], [1])
    assert state.basis == [0]
    assert_allclose(state.A, [[1]])
    assert state.removed_rows == []


def test_redundancy_checks_augmented_rhs_not_only_matrix_rank():
    p = LP([1], [[1], [2]], [1, 3], ['=', '='])
    result = solve(p, method='simplex')
    assert result.status == 'infeasible'
    assert result.phase_one_objective > 0


@pytest.mark.parametrize('p,x,value', [
    (LP([-3, -2], [[1, 1], [1, 0], [0, 1]], [4, 2, 3], ['<='] * 3), [2, 2], -10),
    (LP([1], [[1], [2]], [1, 2], ['=', '=']), [1], 1),
    (LP([-1, -1], [[1, 0], [0, 1], [1, 1]], [1, 1, 1], ['<='] * 3), None, -1),
    (LP([0], [[1]], [0], ['=']), [0], 0),
    (LP([1], np.empty((0, 1)), [], []), [0], 0),
])
def test_finite_optima_including_degeneracy_dependency_and_empty_rows(p, x, value):
    result = solve(p, method='simplex')
    assert result.status == 'optimal'
    if x is not None:
        assert_allclose(result.x, x, atol=1e-8)
    assert result.objective == pytest.approx(value, abs=1e-8)


def test_phase_one_positive_sum_certifies_infeasibility():
    result = solve(LP([0], [[1], [1]], [1, 2], ['>=', '<='], bounds=[(0, 0.5)]),
                   method='simplex')
    assert result.status == 'infeasible'
    assert result.phase_one_objective > 1e-8
    assert np.sum(result.artificial_values) == pytest.approx(result.phase_one_objective)


def test_unbounded_feasible_point_and_improving_ray():
    # min -x-y, x-y=1: x0=(1,0), ray=(1,1).
    result = solve(LP([-1, -1], [[1, -1]], [1], ['=']), method='simplex')
    assert result.status == 'unbounded'
    assert result.objective is None
    assert_allclose(np.array([[1, -1]]) @ result.x, [1], atol=1e-8)
    d = result.ray
    assert np.min(result.x) >= -1e-8
    assert np.min(d) >= -1e-8
    assert_allclose(np.array([[1, -1]]) @ d, [0], atol=1e-8)
    assert np.dot([-1, -1], d) < -1e-8


def test_blands_rule_escapes_course_cycling_example():
    # Cycling coefficients from the course notes (section 8); bound 1, attained
    # at (1,0,1,0). No fixed pivot count is imposed.
    p = LP([10, -57, -9, -24], [[.5, -5.5, -2.5, 9], [.5, -1.5, -.5, 1], [1, 0, 0, 0]],
           [0, 0, 1], ['<='] * 3, sense='max')
    result = solve(p, method='simplex', options=Options(max_iter=100))
    assert result.status == 'optimal'
    assert result.objective == pytest.approx(1)


def test_singular_basis_is_explicit_numerical_exception():
    with pytest.raises(np.linalg.LinAlgError):
        basis_state(np.array([[1., 2], [2, 4]]), np.array([1., 2]), np.ones(2), [0, 1])


def test_removed_row_evidence_preserves_augmented_dependence():
    result = solve(LP([1], [[1], [2]], [1, 2], ['=', '=']), method='simplex')
    assert len(result.removed_rows) == 1
    evidence = result.removed_rows[0]
    original_augmented = np.array([[1., 1], [2, 2]])
    assert_allclose(evidence.weights @ original_augmented, [0, 0], atol=1e-8)
    assert abs(evidence.weights[evidence.row]) > 1e-8


def test_zero_row_with_nonzero_rhs_is_infeasible():
    assert solve(LP([1], [[0]], [1], ['=']), method='simplex').status == 'infeasible'


def test_zero_redundant_equality_does_not_block_optimum():
    result = solve(LP([1], [[0], [1]], [0, 2], ['=', '=']), method='simplex')
    assert result.status == 'optimal'
    assert result.objective == pytest.approx(2)
    assert len(result.removed_rows) == 1


def test_unconstrained_improving_nonnegative_variable_is_unbounded():
    result = solve(LP([-1], np.empty((0, 1)), [], []), method='simplex')
    assert result.status == 'unbounded'
    assert result.ray[0] > 0


def test_alternate_optimum_has_zero_nonbasic_reduced_cost():
    result = solve(LP([-1, -1], [[1, 1]], [1], ['=']), method='simplex')
    assert result.status == 'optimal'
    assert result.objective == pytest.approx(-1)
    nonbasic = set(range(2)) - set(result.basis)
    assert len(nonbasic) == 1
    assert abs(result.reduced_costs[nonbasic.pop()]) <= 1e-8


def test_bad_basis_duplicate_indices_is_input_error():
    with pytest.raises(ValueError):
        basis_state(np.eye(2), np.ones(2), np.ones(2), [0, 0])


def test_basis_inverse_is_recomputed_when_matrix_changes():
    A = np.eye(2)
    first = basis_state(A, np.array([2., 3]), np.ones(2), [0, 1])
    A[0, 0] = 2
    second = basis_state(A, np.array([2., 3]), np.ones(2), [0, 1])
    assert_allclose(first.inverse, np.eye(2))
    assert_allclose(second.inverse, [[.5, 0], [0, 1]])
    assert_allclose(second.basic_values, [1, 3])


def test_all_zero_redundant_row_is_removed_with_artificial_column():
    state = remove_artificials(np.array([[0., 1]]), np.array([0.]), [1], [1])
    assert state.A.shape == (0, 1)
    assert len(state.b) == 0 and state.basis == []
    assert len(state.removed_rows) == 1


def test_phase_one_known_positive_optimum_is_one():
    # min a1+a2, x+a1=1, x+a2=2, all nonnegative => a2-a1=1.
    result = solve(LP([0], [[1], [1]], [1, 2], ['=', '=']), method='simplex')
    assert result.status == 'infeasible'
    assert result.phase_one_objective == pytest.approx(1., abs=1e-8)
    assert_allclose(result.artificial_values, [0, 1], atol=1e-8)
