"""Primal-dual signs and literal Newton solution checked independently."""
import numpy as np
import pytest
from numpy.testing import assert_allclose
from lp_solver import (LP, Options, solve, residuals, newton_direction,
                       fraction_step, validate_start, centered_target, converged)


def test_primal_dual_residuals_objectives_and_average_complementarity():
    state = residuals(np.array([[1., 1]]), np.array([3.]), np.array([1., 2]),
                      np.array([1., 1]), np.array([.5]), np.array([2., 3]))
    assert_allclose(state.primal, [-1])
    assert_allclose(state.dual, [1.5, 1.5])
    assert state.mu == pytest.approx(2.5)
    assert state.primal_objective == pytest.approx(3)
    assert state.dual_objective == pytest.approx(1.5)


def test_newton_direction_satisfies_all_three_block_equations():
    # A dx=-rp; A^T dy+ds=-rd; S dx+X ds=sigma*mu*e-XSe.
    A = np.array([[1., 1]])
    x, y, s = np.ones(2), np.array([0.]), np.ones(2)
    dx, dy, ds = newton_direction(A, np.array([3.]), np.array([1., 2]), x, y, s, sigma=.5)
    assert_allclose(dx, [1., 0.], atol=1e-12)
    assert_allclose(dy, [1.5], atol=1e-12)
    assert_allclose(ds, [-1.5, -.5], atol=1e-12)
    assert_allclose(A @ dx, [1.], atol=1e-12)
    assert_allclose(A.T @ dy + ds, [0., 1.], atol=1e-12)
    assert_allclose(s * dx + x * ds, [-.5, -.5], atol=1e-12)


def test_centering_target_is_sigma_times_average_not_affine_scaling():
    assert_allclose(centered_target(np.array([1., 2]), np.array([3., 1]), sigma=.4), [1., 1.])


@pytest.mark.parametrize('v,d,expected', [
    ([2, 3], [-4, 1], .495), ([2, 3], [0, 1], 1.),
    ([2, 3], [-.1, -.1], 1.), ([2, 3], [-2, -6], .495),
])
def test_fraction_to_boundary_is_capped_and_strictly_positive(v, d, expected):
    alpha = fraction_step(np.array(v, float), np.array(d, float), fraction=.99)
    assert alpha == pytest.approx(expected)
    assert np.min(np.array(v) + alpha * np.array(d)) > 0


@pytest.mark.parametrize('x,y,s', [
    ([0, 1], [0], [1, 1]), ([-1, 1], [0], [1, 1]),
    ([1, 1], [0], [0, 1]), ([1, 1], [0], [-1, 1]),
    ([np.inf, 1], [0], [1, 1]), ([1, 1], [np.nan], [1, 1]),
    ([1], [0], [1, 1]), ([1, 1], [0, 0], [1, 1]),
    ([1, 1], [0], [1]),
])
def test_interior_start_rejects_nonpositive_nonfinite_and_wrong_shapes(x, y, s):
    with pytest.raises(ValueError):
        validate_start(np.array([[1., 1]]), np.array(x), np.array(y), np.array(s))


def test_infeasible_positive_start_needs_no_feasibility_solve():
    validate_start(np.array([[1., 1]]), np.array([3., 4]), np.array([-2.]), np.array([5., 6]))


def test_rank_deficient_ip_input_is_unsupported_not_infeasible():
    with pytest.raises(ValueError):
        solve(LP([1], [[1], [2]], [1, 2], ['=','=']), method='interior',
              start=(np.array([3.]), np.array([0., 0]), np.array([2.])))


@pytest.mark.parametrize('start', [([1., 1], [0.], [1., 1]),
                                  ([100., .01], [-20.], [.1, 40.])])
def test_two_distinct_infeasible_starts_reach_same_known_optimum(start):
    # min x+2y, x+y=3: x=(3,0), dual y=1, s=(0,1).
    result = solve(LP([1, 2], [[1, 1]], [3], ['=']), method='interior',
                   start=tuple(np.array(a) for a in start))
    assert result.status == 'optimal'
    assert_allclose(result.x, [3, 0], atol=1e-6)
    assert result.objective == pytest.approx(3, abs=1e-6)
    assert_allclose(result.y, [1], atol=1e-6)
    assert_allclose(result.s, [0, 1], atol=1e-6)


def test_ip_logs_recompute_residuals_and_keep_every_iterate_interior():
    result = solve(LP([1, 2], [[1, 1]], [3], ['=']), method='interior',
                   start=(np.ones(2), np.zeros(1), np.ones(2)))
    assert result.iterations
    for row in result.iterations:
        assert np.min(row.x) > 0 and np.min(row.s) > 0
        assert_allclose(row.primal_residual, [sum(row.x)-3], atol=1e-12)
        assert_allclose(row.dual_residual, row.y[0] + row.s - [1, 2], atol=1e-12)
        assert row.mu == pytest.approx(row.x @ row.s / 2)
        assert row.primal_objective == pytest.approx(row.x @ [1, 2])
        assert row.dual_objective == pytest.approx(3*row.y[0])
        assert 0 < row.sigma < 1
        assert 0 <= row.primal_step <= 1 and 0 <= row.dual_step <= 1
        assert row.diagnostics.primal_norm == pytest.approx(abs(sum(row.x)-3))
        assert row.diagnostics.normalized_primal == pytest.approx(abs(sum(row.x)-3)/4)
        assert row.diagnostics.normalized_dual == pytest.approx(
            np.max(np.abs(row.y[0] + row.s - [1, 2]))/3)
        denom = 1+abs(row.x @ [1, 2])+abs(3*row.y[0])
        assert row.diagnostics.normalized_gap == pytest.approx(
            abs(row.x @ [1, 2]-3*row.y[0])/denom)


def test_first_centered_update_uses_separate_primal_and_dual_steps():
    result = solve(LP([1, 2], [[1, 1]], [3], ['=']), method='interior',
                   start=(np.ones(2), np.zeros(1), np.ones(2)),
                   options=Options(sigma=.5, fraction=.99))
    assert len(result.iterations) >= 2
    first, second = result.iterations[:2]
    assert_allclose(first.x, [1, 1])
    assert_allclose(second.x, [2, 1], atol=1e-12)
    assert_allclose(second.y, [.99], atol=1e-12)
    assert_allclose(second.s, [.01, .67], atol=1e-12)
    assert first.primal_step == pytest.approx(1)
    assert first.dual_step == pytest.approx(.66)


def test_fixed_sigma_is_configurable_in_iteration_log():
    result = solve(LP([1, 2], [[1, 1]], [3], ['=']), method='interior',
                   start=(np.ones(2), np.zeros(1), np.ones(2)), options=Options(sigma=.3))
    assert result.iterations
    assert all(row.sigma == pytest.approx(.3) for row in result.iterations)


def test_newton_singular_system_raises_numerical_exception():
    with pytest.raises(np.linalg.LinAlgError):
        newton_direction(np.array([[1., 1], [2, 2]]), np.array([3., 6]),
                         np.array([1., 2]), np.ones(2), np.zeros(2), np.ones(2), sigma=.5)
