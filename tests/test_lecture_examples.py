"""Course examples: slides (Good/Bad/Ugly) and lecture notes (sections 1, 5-9).

The notes number variables from 1; arrays here are 0-based, so notes basis
(3,1) is [2, 0]. Our pivot rule is Bland's (both parts). Where a notes trace
used Dantzig's entering rule, the test says so and pins only what Bland gives;
other pivot rules may legitimately visit different bases, so the end results
(status, optimal value, certificates) are also asserted separately.
"""
import numpy as np
import pytest
from numpy.testing import assert_allclose
from lp_solver import (LP, Options, solve, to_standard, basis_state, bland_enter,
                       bland_leave, phase_one, remove_artificials, rank_diagnostics)

BLAND = dict(pivot_tol=1e-12, tie_atol=1e-10, tie_rtol=1e-9, feas_tol=1e-8)


def trace_is_consistent(result):
    """Rule-independent checks on every logged simplex state."""
    for row in result.iterations:
        assert len(set(row.basis)) == len(row.basis)
        assert_allclose(row.A @ row.x, row.b, atol=1e-8)
        assert np.min(row.x) >= -1e-8
        B = row.A[:, row.basis]
        assert_allclose(B @ row.x[row.basis], row.b, atol=1e-8)
        y = np.linalg.solve(B.T, row.c[row.basis])
        assert_allclose(row.reduced_costs, row.c - row.A.T @ y, atol=1e-8)


# ---- Notes section 1 and 5: basis bookkeeping and the bounded example --------

A5 = np.array([[1., 1, 1, 0], [2, 1, 0, 1]])
B5 = np.array([4., 5])
C5 = np.array([-3., -2, 0, 0])


@pytest.mark.parametrize('basis,inverse,x_b,y,reduced', [
    ([2, 3], [[1, 0], [0, 1]], [4, 5], [0, 0], [-3, -2, 0, 0]),
    ([2, 0], [[1, -.5], [0, .5]], [1.5, 2.5], [0, -1.5], [0, -.5, 0, 1.5]),
    ([1, 0], [[2, -1], [-1, 1]], [3, 1], [-1, -1], [0, 0, 1, 1]),
    # Notes 1.3: an invertible basis whose basic solution is infeasible (x4=-3). The
    # bookkeeping must report it, not reject it; deciding feasibility is the caller's job.
    ([0, 3], [[1, 0], [-2, 1]], [4, -3], [-3, 0], [0, 1, 3, 0]),
])
def test_notes_basis_inverse_values_multipliers_and_reduced_costs(basis, inverse, x_b, y, reduced):
    state = basis_state(A5, B5, C5, basis)
    assert_allclose(state.inverse, inverse, atol=1e-12)
    assert_allclose(state.basic_values, x_b, atol=1e-12)
    assert_allclose(state.y, y, atol=1e-12)
    assert_allclose(state.reduced_costs, reduced, atol=1e-12)


BOUNDED = LP([3, 2], [[1, 1], [2, 1]], [4, 5], ['<=', '<='], sense='max')


def test_notes_bounded_example_optimum_and_certificate():
    result = solve(BOUNDED, method='simplex')
    assert result.status == 'optimal'
    assert_allclose(result.x, [1, 3], atol=1e-9)
    assert result.objective == pytest.approx(9)          # profit; min value is -9
    assert_allclose(result.standard_x, [1, 3, 0, 0], atol=1e-9)
    assert_allclose(result.y, [-1, -1], atol=1e-9)
    assert_allclose(result.s, [0, 0, 1, 1], atol=1e-9)    # -3x1-2x2 = -9 + x3 + x4
    trace_is_consistent(result)


def test_notes_bounded_trace_under_bland():
    # The notes use Dantzig; here the only negative reduced costs force the same
    # choices (x1 since -3<-2 and index 1<2, then x2 alone), so Bland agrees.
    result = solve(BOUNDED, method='simplex')
    rows = result.iterations
    assert {r.phase for r in rows} == {2}                 # slack identity: Phase I skipped
    assert [list(r.basis) for r in rows] == [[2, 3], [2, 0], [1, 0]]
    assert [r.entering for r in rows[:2]] == [0, 1]
    assert [r.leaving for r in rows[:2]] == [3, 2]
    assert_allclose([r.step for r in rows[:2]], [2.5, 3])
    assert_allclose([r.objective for r in rows], [0, -7.5, -9])
    assert_allclose(rows[1].reduced_costs, [0, -.5, 0, 1.5])


# ---- Notes section 6: unbounded objective, and unbounded region != unbounded objective --

def test_notes_unbounded_example_ray():
    result = solve(LP([-1, -1], [[1, -1]], [1], ['<=']), method='simplex')
    assert result.status == 'unbounded'
    assert result.objective is None
    # Bland's first move is x1 with step 1; then x2 has u=[-1] and no leaving row.
    assert_allclose(result.standard_x, [1, 0, 0], atol=1e-9)
    assert_allclose(result.ray, [1, 1, 0], atol=1e-9)
    assert_allclose(np.array([[1., -1, 1]]) @ result.ray, [0], atol=1e-9)
    assert np.dot([-1, -1, 0], result.ray) == pytest.approx(-2)
    trace_is_consistent(result)


def test_notes_unbounded_region_with_bounded_objective():
    result = solve(LP([1, 1], [[1, -1]], [1], ['<=']), method='simplex')
    assert result.status == 'optimal'
    assert_allclose(result.x, [0, 0], atol=1e-9)
    assert result.objective == pytest.approx(0, abs=1e-9)


# ---- Notes section 7.2: a zero-length pivot at an optimal degenerate point ---

def test_notes_degenerate_zero_length_pivot_reveals_certificate():
    result = solve(LP([-1, 0], [[1, 1]], [0], ['=']), method='simplex')
    assert result.status == 'optimal'
    assert_allclose(result.x, [0, 0], atol=1e-12)
    assert result.objective == pytest.approx(0, abs=1e-12)
    rows = result.iterations
    assert {r.phase for r in rows} == {2}                 # x2 is already a feasible basis
    assert list(rows[0].basis) == [1] and rows[0].entering == 0 and rows[0].leaving == 1
    assert rows[0].step == pytest.approx(0)               # basis changes, point does not
    assert_allclose(rows[0].x, rows[-1].x)
    assert list(rows[-1].basis) == [0]
    assert rows[-1].reduced_costs[1] == pytest.approx(1)  # new basis passes the test
    trace_is_consistent(result)


# ---- Notes sections 8-9: cycling data and Bland's rule ----------------------

CYCLE_A = np.array([[.5, -5.5, -2.5, 9, 1, 0, 0],
                    [.5, -1.5, -.5, 1, 0, 1, 0],
                    [1, 0, 0, 0, 0, 0, 1]])
CYCLE_B = np.array([0., 0, 1])
CYCLE_C = np.array([-10., 57, 9, 24, 0, 0, 0])
CYCLE_MAX_FORM = LP([10, -57, -9, -24], CYCLE_A[:, :4], CYCLE_B, ['<='] * 3, sense='max')


def test_notes_cycling_example_conversion_reproduces_standard_form():
    q = to_standard(CYCLE_MAX_FORM)
    assert_allclose(q.A, CYCLE_A)
    assert_allclose(q.b, CYCLE_B)
    assert_allclose(q.c, CYCLE_C)


def test_notes_cycling_example_bland_trace():
    # Dantzig's entering rule cycles through the first six bases (notes 8.8). Bland agrees
    # for five pivots, then takes x1 instead of x6 at basis (5,4,7). Other rules may
    # take other routes; this pins Bland's route only.
    result = solve(CYCLE_MAX_FORM, method='simplex', options=Options(max_iter=100))
    assert result.status == 'optimal'
    rows = result.iterations
    assert {r.phase for r in rows} == {2}
    assert [list(r.basis) for r in rows] == [
        [4, 5, 6], [0, 5, 6], [0, 1, 6], [2, 1, 6], [2, 3, 6], [4, 3, 6], [4, 0, 6], [4, 0, 2]]
    assert [r.entering for r in rows[:-1]] == [0, 1, 2, 3, 4, 0, 2]
    assert [r.leaving for r in rows[:-1]] == [4, 5, 0, 1, 2, 3, 6]
    assert_allclose([r.step for r in rows[:-1]], [0, 0, 0, 0, 0, 0, 1], atol=1e-12)
    assert_allclose(rows[0].x, [0, 0, 0, 0, 0, 0, 1])     # six pivots, same point
    assert_allclose(rows[5].x, rows[0].x)
    assert_allclose(rows[5].reduced_costs[[0, 1, 2, 5]], [-22, 93, 21, -24])
    assert_allclose(result.standard_x, [1, 0, 1, 0, 2, 0, 0], atol=1e-9)
    assert result.objective == pytest.approx(1)           # max form; min value is -1
    assert_allclose(result.y, [0, -18, -1], atol=1e-9)
    assert_allclose(result.reduced_costs, [0, 30, 0, 42, 0, 18, 1], atol=1e-9)
    trace_is_consistent(result)


def test_notes_cycling_example_any_rule_must_still_reach_optimum_one():
    # Rule-independent end result: bound 1 from multipliers (0,18,1), attained at (1,0,1,0).
    result = solve(CYCLE_MAX_FORM, method='simplex', options=Options(max_iter=100))
    assert result.status == 'optimal'
    assert result.objective == pytest.approx(1)
    assert_allclose(result.x, [1, 0, 1, 0], atol=1e-9)


@pytest.mark.parametrize('values,direction,basis,row,step', [
    ([0, 0, 1], [.5, .5, 1], [5, 6, 7], 0, 0),            # iteration 0: x5 beats x6
    ([0, 0, 1], [-11, 4, 11], [1, 6, 7], 1, 0),           # iteration 1: x6 at ratio 0
    ([0, 0, 1], [.5, .5, -.5], [1, 2, 7], 0, 0),          # iteration 2: x1 beats x2
    ([0, 0, 1], [-8, 2, 0], [3, 2, 7], 1, 0),             # iteration 3: only x2 eligible
    ([0, 0, 1], [.5, .25, 0], [3, 4, 7], 0, 0),           # iteration 4: x3 beats x4
    ([0, 0, 1], [-4, .5, 1], [5, 4, 7], 1, 0),            # Bland entering x1: x4 leaves
    ([0, 0, 1], [1, 1, 1], [8, 2, 5], 1, 0),              # notes 9.1: x2 in row 2 beats x8
])
def test_notes_leaving_choice_uses_variable_index_among_ratio_ties(
        values, direction, basis, row, step):
    got = bland_leave(np.array(values, float), np.array(direction, float), basis, **BLAND)
    assert got[0] == row and got[1] == pytest.approx(step)


def test_notes_bland_entering_prefers_smallest_index_over_most_negative():
    # Basis (5,4,7): reduced costs of x1,x2,x3,x6 are (-22,93,21,-24). Dantzig picks x6.
    costs = np.array([-22., 93, 21, -24])
    assert bland_enter(costs, [1, 2, 3, 6], tolerance=1e-9) == 1
    assert bland_enter(np.array([27., -1, 44, 20]), [2, 3, 4, 6], tolerance=1e-9) == 3


# ---- Slides: Good / Bad / Ugly ---------------------------------------------

def test_good_identity_present_skips_phase_one():
    # Skipping is valid because the slack columns already form I_2 with b >= 0, so the
    # Phase I objective (sum of artificials) has nothing to minimize.
    result = solve(LP([-1, -2], [[1, 1], [-1, 2]], [4, 2], ['<=', '<=']), method='simplex')
    assert result.status == 'optimal'
    assert_allclose(result.x, [2, 2], atol=1e-9)
    assert result.objective == pytest.approx(-6)
    assert {r.phase for r in result.iterations} == {2}
    assert list(result.iterations[0].basis) == [2, 3]
    trace_is_consistent(result)


BAD = LP([2, 3], [[1, 1], [1, 2], [2, 1]], [2, 3, 6], ['>=', '=', '<='])


def test_bad_conversion_matches_slides():
    q = to_standard(BAD)
    assert_allclose(q.A, [[1, 1, -1, 0], [1, 2, 0, 0], [2, 1, 0, 1]])
    assert_allclose(q.b, [2, 3, 6])
    assert_allclose(q.c, [2, 3, 0, 0])


def test_bad_adds_artificials_only_to_rows_without_unit_columns():
    result = solve(BAD, method='simplex')
    assert result.status == 'optimal'
    assert_allclose(result.x, [1, 1], atol=1e-9)
    assert result.objective == pytest.approx(5)
    phase1 = [r for r in result.iterations if r.phase == 1]
    assert phase1, 'Phase I is required: only e3 is present'
    assert phase1[0].A.shape == (3, 6)                    # x5a, x6a appended; none for row 3
    assert list(phase1[0].basis) == [4, 5, 3]             # {x5a, x6a, x4}
    assert_allclose(phase1[0].c, [0, 0, 0, 0, 1, 1])
    assert all(r.A.shape[1] == 4 for r in result.iterations if r.phase == 2)
    trace_is_consistent(result)


UGLY_A = np.array([[1., 1, 1], [1, 2, 3], [2, 3, 4]])


def ugly(b3=11.):
    return LP([1, 2, 3], UGLY_A, [4, 7, b3], ['='] * 3)


def test_ugly_rank_is_deficient_not_infeasible():
    assert rank_diagnostics(UGLY_A, Options()) == 'deficient'
    assert rank_diagnostics(np.eye(3), Options()) == 'full_row_rank'


def test_ugly_dependent_row_is_removed_with_evidence():
    result = solve(ugly(), method='simplex')
    assert result.status == 'optimal'
    assert result.objective == pytest.approx(7)           # equals row 2, so every feasible point is optimal
    assert_allclose(UGLY_A @ result.x, [4, 7, 11], atol=1e-8)
    assert np.min(result.x) >= -1e-8
    assert {r.phase for r in result.iterations} == {1, 2}
    assert len(result.removed_rows) == 1
    evidence = result.removed_rows[0]
    augmented = np.column_stack([UGLY_A, [4., 7, 11]])
    assert_allclose(evidence.weights @ augmented, np.zeros(4), atol=1e-8)
    assert abs(evidence.weights[evidence.row]) > 1e-8
    trace_is_consistent(result)


def test_ugly_inconsistent_rhs_is_infeasible():
    result = solve(ugly(b3=12.), method='simplex')
    assert result.status == 'infeasible'
    assert result.phase_one_objective > 1e-8


def test_ugly_interior_rejects_dependent_rows_as_unsupported():
    with pytest.raises(ValueError):
        solve(ugly(), method='interior', start=(np.ones(3), np.zeros(3), np.ones(3)))


def test_artificial_cleanup_removes_zero_artificial_in_dependent_row():
    # Phase I state for the Ugly LP: basis x1, x2 and artificial a3 (column 5) at zero,
    # since row3 - row1 - row2 vanishes on every real column.
    A = np.hstack([UGLY_A, np.eye(3)])
    b = np.array([4., 7, 11])
    state = remove_artificials(A, b, [0, 1, 5], [3, 4, 5])
    assert state.basis == [0, 1]
    assert_allclose(state.A, UGLY_A[:2])
    assert_allclose(state.b, [4, 7])
    assert len(state.removed_rows) == 1
    evidence = state.removed_rows[0]
    assert evidence.row == 2
    assert_allclose(evidence.weights @ np.column_stack([UGLY_A, b]), np.zeros(4), atol=1e-12)
    assert abs(evidence.weights[2]) > 1e-8


def test_dependent_rows_with_partial_identity_and_negative_rhs_variant():
    # Rows 1-2 are dependent (row2 = 2*row1); e3 supplies row 3's basis. Optimum x=(1,0,3).
    lp = LP([1, 2, 1], [[1, 1, 0], [2, 2, 0], [0, 0, 1]], [1, 2, 3], ['='] * 3)
    result = solve(lp, method='simplex')
    assert result.status == 'optimal'
    assert result.objective == pytest.approx(4)
    assert len(result.removed_rows) == 1
    # Same constraints written with negative right-hand sides must give the same answer.
    flipped = LP([1, 2, 1], [[-1, -1, 0], [-2, -2, 0], [0, 0, -1]], [-1, -2, -3], ['='] * 3)
    again = solve(flipped, method='simplex')
    assert again.status == 'optimal'
    assert again.objective == pytest.approx(4)
    assert len(again.removed_rows) == 1


def test_negative_rhs_surplus_reuse_starts_without_phase_one():
    # -x1-2x2 >= -4 has surplus -1 and rhs -4; normalizing the row gives x1+2x2+s=4,
    # a feasible slack basis, so Phase I is skipped. Optimum (4,0), value -4.
    result = solve(LP([-1, -1], [[-1, -2]], [-4], ['>=']), method='simplex')
    assert result.status == 'optimal'
    assert_allclose(result.x, [4, 0], atol=1e-9)
    assert result.objective == pytest.approx(-4)
    assert {r.phase for r in result.iterations} == {2}


def test_negative_rhs_equality_needs_phase_one_and_solves():
    result = solve(LP([1, 1], [[-1, -1]], [-3], ['=']), method='simplex')
    assert result.status == 'optimal'
    assert result.objective == pytest.approx(3)
    assert 1 in {r.phase for r in result.iterations}
