"""Joint stopping, scaling and explicit failure contracts, not algorithms."""
import numpy as np
import pytest
from lp_solver import (Options, residuals, converged, validate_options,
                       validate_start, rank_diagnostics)


def test_raw_and_normalized_diagnostics_use_documented_denominators():
    r = residuals(np.array([[1., 1]]), np.array([3.]), np.array([1., 2]),
                  np.ones(2), np.array([.5]), np.array([2., 3]))
    assert r.primal_norm == pytest.approx(1)
    assert r.dual_norm == pytest.approx(1.5)
    assert r.normalized_primal == pytest.approx(.25)
    assert r.normalized_dual == pytest.approx(.5)
    assert r.normalized_mu == pytest.approx(2.5/5.5)
    assert r.objective_gap == pytest.approx(1.5)
    assert r.normalized_gap == pytest.approx(1.5/5.5)


def test_feasible_positive_start_is_accepted_by_general_api():
    validate_start(np.array([[1., 1]]), np.array([1., 2]), np.array([0.]), np.array([1., 2]))


def test_exact_kkt_point_satisfies_stopping_checks():
    assert converged(np.array([[1., 1]]), np.array([3.]), np.array([1., 2]),
                     np.array([3., 0]), np.array([1.]), np.array([0., 1]), Options())


@pytest.mark.parametrize('x,y,s', [
    ([2., 0], [1.], [0., 1]),  # complementarity zero but primal infeasible
    ([3., 0], [0.], [0., 1]),  # complementarity zero but dual infeasible
    ([1., 2], [0.], [1., 2]),  # feasible equalities but positive complementarity
    ([np.nan, 0], [1.], [0., 1]),
    ([3., 0], [np.inf], [0., 1]),
])
def test_small_mu_alone_or_nonfinite_data_never_establishes_optimality(x, y, s):
    assert not converged(np.array([[1., 1]]), np.array([3.]), np.array([1., 2]),
                         np.array(x), np.array(y), np.array(s), Options())


def test_normalized_gap_is_independent_guard_beyond_average_complementarity():
    # n=10: mu=1e-8, but absolute gap=1e-7 and normalized gap~1e-7.
    # primal=dual residual=0. mu passes 2e-8 while total objective gap fails.
    assert not converged(np.ones((1, 10)), np.array([1.]), np.full(10, 1e-7),
                         np.full(10, .1), np.array([0.]), np.full(10, 1e-7),
                         Options(gap_tol=2e-8))


def test_normalized_mu_is_checked_even_if_gap_tolerance_is_met():
    # Deliberately loose dual tolerance permits rd=1; objective gap is zero,
    # but normalized mu=1/3 must still fail. Exact feasible KKT data have
    # gap=n*mu, so they cannot isolate this guard with a common gap tolerance.
    assert not converged(np.array([[1.]]), np.array([1.]), np.array([1.]),
                         np.array([1.]), np.array([1.]), np.array([1.]),
                         Options(opt_tol=1., gap_tol=.2))


def test_large_objectives_cannot_hide_large_primal_residual():
    assert not converged(np.array([[1.]]), np.array([1.]), np.array([1e12]),
                         np.array([2.]), np.array([1e12]), np.array([0.]), Options())


def test_tolerance_is_configurable_and_boundary_is_inclusive():
    # Binary-exact rp/(1+|b|)=.03125/2=1/64; rd=0.
    args = (np.array([[1.]]), np.array([1.]), np.array([1.]),
            np.array([1.03125]), np.array([1.]), np.array([0.]))
    assert converged(*args, Options(feas_tol=1/64, gap_tol=.02))
    assert not converged(*args, Options(feas_tol=.015, gap_tol=.02))


def test_zero_residuals_and_gap_do_not_excuse_negative_primal_variables():
    assert not converged(np.array([[1.]]), np.array([-1.]), np.array([0.]),
                         np.array([-1.]), np.array([0.]), np.array([0.]), Options())


def test_zero_residuals_and_gap_do_not_excuse_negative_dual_slacks():
    assert not converged(np.array([[1., 0]]), np.array([1.]), np.array([0., -1.]),
                         np.array([1., 0.]), np.array([0.]), np.array([0., -1.]), Options())


def test_solver_stopping_rejects_negative_basic_value_with_zero_complementarity():
    assert not converged(np.eye(2), np.array([-1., 2]), np.zeros(2),
                         np.array([-1., 2]), np.zeros(2), np.zeros(2), Options())


def test_nonnegativity_tolerance_is_explicit_and_configurable():
    args = (np.array([[1., 1]]), np.array([1.-1e-10]), np.zeros(2),
            np.array([-1e-10, 1.]), np.zeros(1), np.zeros(2))
    assert converged(*args, Options(feas_tol=1e-8))
    assert not converged(*args, Options(feas_tol=1e-12))


@pytest.mark.parametrize('change', [
    {'feas_tol': 0}, {'opt_tol': -1}, {'gap_tol': np.nan},
    {'pivot_tol': np.inf}, {'rank_tol': -1}, {'sigma': 0}, {'sigma': 1},
    {'fraction': 0}, {'fraction': 1}, {'max_iter': -1}, {'max_iter': 1.5},
    {'tie_atol': -1}, {'tie_rtol': np.nan},
])
def test_invalid_numerical_options_are_input_errors(change):
    with pytest.raises(ValueError):
        validate_options(Options(**change))


def test_valid_configurable_options_are_accepted():
    validate_options(Options(feas_tol=1e-7, opt_tol=1e-9, gap_tol=1e-6, sigma=.2,
                             fraction=.9, max_iter=0))


@pytest.mark.parametrize('scale', [1e-20, 1., 1e20])
def test_rank_assessment_is_invariant_under_uniform_scaling(scale):
    assert rank_diagnostics(scale*np.eye(2), Options()) == 'full_row_rank'


def test_exact_dependent_rows_report_rank_deficiency_not_infeasibility():
    assert rank_diagnostics(np.array([[1., 2], [2, 4]]), Options()) == 'deficient'


def test_rank_at_cutoff_is_uncertain_not_a_proof_of_infeasibility():
    # Dyadic values keep the cutoff exact: .25*max(2,2)*1 = .5 = smaller singular value.
    assert rank_diagnostics(np.diag([1., .5]), Options(rank_tol=.25)) == 'uncertain'
