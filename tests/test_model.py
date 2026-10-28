"""General LP boundary and original-to-standard correspondence contracts."""
import numpy as np
import pytest
from numpy.testing import assert_allclose
from lp_solver import LP, validate, to_standard, assignment_size, solve


@pytest.mark.parametrize('changes', [
    {'c': [[1, 2]]}, {'A': [1, 2]}, {'A': [[1]]}, {'b': [1, 2]},
    {'b': [[1]]}, {'relations': []}, {'relations': ['<']},
    {'bounds': [(0, None)]}, {'bounds': [(2, 1), (0, None)]},
    {'bounds': [(np.nan, None), (0, None)]},
    {'bounds': [(np.inf, None), (0, None)]},
    {'bounds': [(0, -np.inf), (0, None)]},
    {'sense': 'maximize-ish'}, {'integrality': [1, 0]},
    {'c': [np.nan, 1]}, {'A': [[1, np.inf]]}, {'b': [np.nan]},
    {'c': [1j, 2]}, {'c': ['one', 'two']},
    {'c': [], 'A': np.empty((0, 0)), 'b': [], 'relations': []},
])
def test_reject_invalid_or_unsupported_input(changes):
    data = dict(c=[1, 2], A=[[1, 1]], b=[1], relations=['<='])
    data.update(changes)
    with pytest.raises(ValueError):
        validate(LP(**data))


def test_validation_accepts_small_continuous_lp_and_does_not_mutate():
    p = LP([1, 2], [[1, 1]], [1], ['<='])
    validate(p)
    assert p.c == [1, 2]
    assert p.A == [[1, 1]]


def test_max_mixed_rows_negative_rhs_and_objective_recovery():
    # min standard objective = -3*x-2*y; second row flips before surplus.
    p = LP([3, 2], [[1, 1], [-1, 0], [0, 1]], [4, -1, 2],
           ['<=', '<=', '='], sense='max')
    q = to_standard(p)
    assert_allclose(q.A, [[1, 1, 1, 0], [1, 0, 0, -1], [0, 1, 0, 0]])
    assert_allclose(q.b, [4, 1, 2])
    assert_allclose(q.c, [-3, -2, 0, 0])
    assert_allclose(q.recover_x([2, 2, 0, 1]), [2, 2])
    assert q.recover_objective(-10) == pytest.approx(10)


@pytest.mark.parametrize('bound,c,z,original,objective', [
    ((2, None), 3, [3], [5], 15),
    ((None, 4), 3, [3], [1], 3),
    ((None, None), 3, [2, 5], [-3], -9),
    ((2, 2), 3, [], [2], 6),
])
def test_bound_substitution_and_objective_offset(bound, c, z, original, objective):
    q = to_standard(LP([c], np.empty((0, 1)), [], [], bounds=[bound]))
    assert_allclose(q.recover_x(z), original)
    assert q.recover_objective(float(np.dot(q.c, z))) == pytest.approx(objective)


def test_finite_interval_adds_upper_bound_row():
    q = to_standard(LP([3], np.empty((0, 1)), [], [], bounds=[(2, 5)]))
    assert_allclose(q.A, [[1, 1]])
    assert_allclose(q.b, [3])
    assert_allclose(q.c, [3, 0])
    assert_allclose(q.recover_x([3, 0]), [5])
    assert q.recover_objective(9) == pytest.approx(15)


def test_max_offset_and_shifted_constraint_rhs():
    q = to_standard(LP([3], [[2]], [10], ['<='], sense='max', bounds=[(2, None)]))
    assert_allclose(q.A, [[2, 1]])
    assert_allclose(q.b, [6])
    assert_allclose(q.c, [-3, 0])
    assert q.recover_objective(-9) == pytest.approx(15)


def test_default_nonnegative_and_empty_rows_preserve_dimension():
    q = to_standard(LP([1, 2], np.empty((0, 2)), [], []))
    assert q.A.shape == (0, 2)
    assert_allclose(q.recover_x([0, 3]), [0, 3])


@pytest.mark.parametrize('n,m,eligible', [(8, 5, True), (7, 5, False), (8, 4, False)])
def test_assignment_size_uses_original_model(n, m, eligible):
    A = np.ones((m, n))
    A[np.arange(m), np.arange(m)] = 2  # distinct rows, each with several variables
    p = LP(np.ones(n), A, np.ones(m), ['<='] * m, bounds=[(None, None)] * n)
    report = assignment_size(p)
    assert report.original_variables == n
    assert report.substantive_constraints == m
    assert report.eligible is eligible


def test_nonnegative_declarations_and_generated_rows_do_not_meet_assignment_size():
    p = LP([1] * 8, np.empty((0, 8)), [], [], bounds=[(0, 1)] * 8)
    assert not assignment_size(p).eligible
    assert assignment_size(p).substantive_constraints == 0


def test_nonnegative_rows_are_not_substantive_assignment_constraints():
    p = LP(np.ones(8), np.eye(8), np.zeros(8), ['>=']*8)
    report = assignment_size(p)
    assert report.substantive_constraints == 0
    assert not report.eligible


def test_unknown_solver_rejected_instead_of_silent_fallback():
    with pytest.raises(ValueError):
        solve(LP([1], [[1]], [1], ['=']), method='typo')


def test_conversion_does_not_mutate_numpy_inputs():
    A, b, c = np.array([[-1.]]), np.array([-2.]), np.array([3.])
    to_standard(LP(c, A, b, ['<='], sense='max'))
    assert_allclose(A, [[-1]])
    assert_allclose(b, [-2])
    assert_allclose(c, [3])


def test_greater_equal_surplus_is_negative():
    q = to_standard(LP([1], [[1]], [2], ['>=']))
    assert_allclose(q.A, [[1, -1]])
    assert_allclose(q.b, [2])
    assert_allclose(q.c, [1, 0])


def test_free_variable_reconstruction_is_many_to_one():
    q = to_standard(LP([2], [[1]], [-3], ['='], bounds=[(None, None)]))
    assert_allclose(q.A, [[-1, 1]])
    assert_allclose(q.b, [3])
    assert_allclose(q.c, [2, -2])
    assert_allclose(q.recover_x([0, 3]), [-3])
    assert_allclose(q.recover_x([2, 5]), [-3])


def test_recovery_rejects_wrong_standard_dimension():
    q = to_standard(LP([1], [[1]], [2], ['<=']))
    with pytest.raises(ValueError):
        q.recover_x([1])
