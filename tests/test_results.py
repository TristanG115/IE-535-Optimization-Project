"""Observable status, trace and certificate contracts across methods."""
import numpy as np
import pytest
from numpy.testing import assert_allclose
from lp_solver import LP, Options, Result, solve, to_standard, validate_options, check_certificate


@pytest.mark.parametrize('method', ['simplex', 'interior'])
def test_zero_iteration_budget_is_limit_never_infeasible_or_optimal(method):
    result = solve(LP([1, 2], [[1, 1]], [3], ['=']), method=method,
                   options=Options(max_iter=0), start=(np.ones(2), np.zeros(1), np.ones(2)))
    assert result.status == 'iteration_limit'
    assert result.message


def test_simplex_trace_contains_both_phases_and_mathematically_consistent_basis():
    result = solve(LP([1, 2], [[1, 1]], [3], ['=']), method='simplex')
    assert {row.phase for row in result.iterations} == {1, 2}
    assert result.message
    for row in result.iterations:
        assert row.iteration >= 0
        assert len(set(row.basis)) == len(row.basis)
        assert_allclose(row.A @ row.x, row.b, atol=1e-8)
        assert row.objective == pytest.approx(row.c @ row.x)
        B = row.A[:, row.basis]
        assert_allclose(B @ row.x[row.basis], row.b, atol=1e-8)
        dual = np.linalg.solve(B.T, row.c[row.basis])
        assert_allclose(row.reduced_costs, row.c - row.A.T @ dual, atol=1e-8)
        if row.entering is not None:
            assert row.leaving in row.basis
            assert row.entering not in row.basis
            assert row.step >= 0
    # Phase II contains no artificial columns; trace arrays must be snapshots.
    assert result.iterations[-1].A.shape[1] == 2
    if len(result.iterations) > 1:
        assert not np.shares_memory(result.iterations[0].x, result.iterations[-1].x)


@pytest.mark.parametrize('method', ['simplex', 'interior'])
def test_optimal_standard_certificate_checks_primal_dual_gap_and_slacks(method):
    A, b, c = np.array([[1., 1]]), np.array([3.]), np.array([1., 2])
    result = solve(LP(c, A, b, ['=']), method=method,
                   start=(np.ones(2), np.zeros(1), np.ones(2)))
    assert result.status == 'optimal'
    assert_allclose(A @ result.standard_x, b, atol=1e-6)
    assert_allclose(A.T @ result.y + result.s, c, atol=1e-6)
    assert min(result.standard_x) >= -1e-8 and min(result.s) >= -1e-8
    assert abs(c @ result.standard_x - b @ result.y) <= 1e-6
    assert check_certificate(A, b, c, result, tolerance=1e-6)


@pytest.mark.parametrize('damage', ['primal', 'dual', 'objective', 'nan'])
def test_certificate_checker_rejects_corrupted_claim(damage):
    # The checker must recompute checks; trusting a stored success flag is unsafe.
    result = Result('optimal', 'literal valid certificate', x=np.array([3., 0]),
                    standard_x=np.array([3., 0]), objective=3.,
                    y=np.array([1.]), s=np.array([0., 1]))
    if damage == 'primal':
        result.standard_x = np.array([4., 0])
    elif damage == 'dual':
        result.s = np.array([-1., 0])
    elif damage == 'objective':
        result.objective = 999.
    else:
        result.standard_x = np.array([np.nan, 0])
    assert not check_certificate(np.array([[1., 1]]), np.array([3.]), np.array([1., 2]),
                                 result, tolerance=1e-8)


@pytest.mark.parametrize('method', ['simplex', 'interior'])
def test_original_max_solution_and_objective_survive_conversion(method):
    result = solve(LP([3], [[1]], [5], ['<='], sense='max', bounds=[(2, None)]),
                   method=method, start=(np.ones(2), np.zeros(1), np.ones(2)))
    assert result.status == 'optimal'
    assert_allclose(result.x, [5], atol=1e-6)
    assert result.objective == pytest.approx(15, abs=1e-6)


@pytest.mark.parametrize('method', ['simplex', 'interior'])
def test_positive_constraint_scaling_keeps_known_solution(method):
    # Row scaling changes conditioning, not the feasible set.
    result = solve(LP([1, 2], [[1e6, 1e6]], [3e6], ['=']), method=method,
                   start=(np.ones(2), np.zeros(1), np.ones(2)))
    assert result.status == 'optimal'
    assert_allclose(result.x, [3, 0], atol=1e-6)
    assert result.objective == pytest.approx(3, abs=1e-6)


def test_certificate_checker_accepts_literal_valid_optimal_certificate():
    result = Result('optimal', 'literal certificate', x=np.array([3., 0]),
                    standard_x=np.array([3., 0]), objective=3.,
                    y=np.array([1.]), s=np.array([0., 1]))
    assert check_certificate(np.array([[1., 1]]), np.array([3.]), np.array([1., 2]),
                             result, tolerance=1e-8)


def test_certificate_checker_accepts_literal_ray_and_rejects_nonimproving_ray():
    result = Result('unbounded', 'literal ray', x=np.array([1., 0]),
                    standard_x=np.array([1., 0]), ray=np.array([1., 1]))
    A, b, c = np.array([[1., -1]]), np.array([1.]), np.array([-1., -1])
    assert check_certificate(A, b, c, result, tolerance=1e-8)
    result.ray = np.zeros(2)
    assert not check_certificate(A, b, c, result, tolerance=1e-8)


def test_optimal_certificate_cannot_omit_nonnegativity_check():
    # Equality, stationarity, objective equality and complementarity all hold.
    # The negative primal entry invalidates the claimed certificate.
    result = Result('optimal', 'invalid negative point', x=np.array([-1., 2]),
                    standard_x=np.array([-1., 2]), objective=0.,
                    y=np.array([0.]), s=np.zeros(2))
    assert not check_certificate(np.array([[1., 1]]), np.array([1.]), np.zeros(2),
                                 result, tolerance=1e-8)


# --- Numerical robustness without prescribing NumPy calls or a status for
# borderline matrices. A returned optimum must survive the independent check
# below; every other outcome only needs a legal status and a message.

def independent_optimal_check(lp, result, tol=1e-6):
    """Scale-aware KKT check that does not call check_certificate."""
    q = to_standard(lp)
    x, y, s = (np.asarray(v, float) for v in (result.standard_x, result.y, result.s))
    for v in (x, y, s, np.asarray(result.x, float), np.asarray(result.objective, float)):
        assert np.all(np.isfinite(v))
    big = lambda v: np.max(np.abs(v), initial=0.)
    assert big(q.A @ x - q.b) <= tol * (1 + big(q.b))
    assert big(q.A.T @ y + s - q.c) <= tol * (1 + big(q.c))
    assert np.min(x, initial=0.) >= -tol * (1 + big(x))
    assert np.min(s, initial=0.) >= -tol * (1 + big(s))
    primal, dual = q.c @ x, q.b @ y
    assert abs(primal - dual) <= tol * (1 + abs(primal) + abs(dual))
    assert result.objective == pytest.approx(q.recover_objective(primal), rel=1e-6, abs=0)


def run(lp, method, start, may_reject=False):
    """Solve; interior may reject near-dependent rows as unsupported input (ValueError)."""
    try:
        return solve(lp, method=method, start=start)
    except ValueError:
        if may_reject and method == 'interior':
            return None
        raise


UNIT_START = (np.ones(2), np.zeros(1), np.ones(2))
HARD = [  # id, LP, start, may_reject, expected objective, expected x (or None)
    ('tiny_pivot', LP([-1], [[1e-14]], [1], ['<=']), UNIT_START, False, -1e14, [1e14]),
    ('huge_scale', LP([1e200, 2e200], [[1e200, 1e200]], [3e200], ['=']),
     UNIT_START, False, 3e200, [3, 0]),
    ('tiny_scale', LP([1e-200, 2e-200], [[1e-200, 1e-200]], [3e-200], ['=']),
     UNIT_START, False, 3e-200, [3, 0]),
    # x1+x2=1 and x1+(1+1e-13)x2=1 force x2=0, so x=(1,0), value 1.
    ('near_dependent', LP([1, 1], [[1, 1], [1, 1 + 1e-13]], [1, 1], ['=', '=']),
     (np.ones(2), np.zeros(2), np.ones(2)), True, 1., None),
]


@pytest.mark.filterwarnings('ignore::RuntimeWarning')
@pytest.mark.parametrize('method', ['simplex', 'interior'])
@pytest.mark.parametrize('name,lp,start,may_reject,objective,x', HARD, ids=[h[0] for h in HARD])
def test_hard_inputs_never_fake_success(name, lp, start, may_reject, objective, x, method):
    result = run(lp, method, start, may_reject)
    if result is None:
        return
    assert result.status in {'optimal', 'numerical_failure', 'iteration_limit'}
    assert result.message
    if result.status == 'optimal':
        independent_optimal_check(lp, result)
        assert result.objective == pytest.approx(objective, rel=1e-6)
        if x is not None:
            assert_allclose(result.x, x, rtol=1e-6, atol=1e-6)


@pytest.mark.parametrize('method', ['simplex', 'interior'])
def test_nearly_dependent_but_feasible_never_reports_infeasible(method):
    # min x1+x2, diag(1, 2e-12) x = (1, 2e-12): the only solution is x=(1,1), value 2.
    lp = LP([1, 1], np.diag([1., 2e-12]), [1., 2e-12], ['=', '='])
    result = run(lp, method, (np.ones(2) * 2, np.zeros(2), np.ones(2)), may_reject=True)
    if result is None:
        return
    assert result.status in {'optimal', 'numerical_failure'}
    assert result.message
    if result.status == 'optimal':
        independent_optimal_check(lp, result)
        assert_allclose(result.x, [1, 1], rtol=1e-6)
        assert result.objective == pytest.approx(2, rel=1e-6)


@pytest.mark.parametrize('method,allowed', [
    ('simplex', {'infeasible', 'numerical_failure'}),
    # Interior makes no infeasibility-certification promise.
    ('interior', {'infeasible', 'numerical_failure', 'iteration_limit'}),
])
def test_nearly_dependent_infeasible_is_never_optimal(method, allowed):
    # Rows (1,1) and (1,1+1e-13) with rhs (1,2): x>=0 and row 1 give x1+x2<=1, so row 2
    # is at most 1+1e-13 while its rhs is 2. The normalized violation is about .3 (1/(1+2)),
    # over 1e7 times feas_tol=1e-8, so this is infeasible by every tolerance used here.
    lp = LP([1, 1], [[1, 1], [1, 1 + 1e-13]], [1, 2], ['=', '='])
    result = run(lp, method, (np.ones(2), np.zeros(2), np.ones(2)), may_reject=True)
    if result is None:
        return
    assert result.status in allowed
    assert result.message
