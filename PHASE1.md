# Phase 1: test contracts for review

Status: tests and interfaces only. Neither solver, converter, validator nor
certificate checker is implemented. Failing tests are intentional requirements,
not expected-failure markers. No tests are skipped. Do not interpret collection
or a stub's presence as implemented numerical functionality.

## Chosen interfaces

The user selected one `lp_solver.py` module with dataclasses and functions, and
the assignment-aligned algorithm contracts. NumPy is the numerical dependency;
pytest runs tests. No SciPy or commercial-solver dependency is introduced.

`LP(c, A, b, relations, sense='min', bounds=None, integrality=None)` represents
original continuous variables. Relations are `<=`, `>=`, `=`; omitted bounds
mean nonnegative variables, and `(None, None)` means unrestricted. Unsupported
integer requirements and malformed/nonfinite data raise ValueError. Lists and
NumPy arrays are accepted without mutation. Empty constraints retain shape
`(0,n)`. Empty objectives are invalid.

`to_standard` returns minimization equality form with nonnegative variables,
an affine variable map and objective sign/offset recovery. Transformation order
is original variables in order (free variable positive part before negative),
then slack/surplus columns in row order; finite bound rows follow input rows.
Fixed variables are eliminated. Normalize negative RHS after substitutions.
Artificial variables belong to Phase I, not the shared converted LP.

Simplex explicitly recomputes the ordered basis inverse. Bland selection uses
stable column IDs. Trace rows describe the state BEFORE their indicated pivot;
terminal rows have no pivot. Removed-row evidence uses weights on original
augmented equality rows, including RHS. IP accepts standard-form x,y,s starts;
the caller uses conversion metadata when the original dimensions differ.

`Result.x` and `objective` use original units; `standard_x`, y, s and recession
certificates use standard units. Malformed/unsupported input raises ValueError.
Iteration limits and numerical failure are separate statuses. IP does not
promise infeasibility/unboundedness certification. Low-level singular linear
algebra raises LinAlgError; solver entry points turn it into numerical_failure.
The certificate checker tests here use identity conversion; checking original
objectives after a general conversion needs mapping metadata in a later stage.

## Approved numerical and initialization choices

The user approved the formulas and defaults, with modifications recorded in
ai_record/decisions.md. Define rp=Ax-b, rd=A^T y+s-c and mu=x^T s/n.
Successful termination requires all of:

- ||rp||inf/(1+||b||inf) <= feas_tol;
- ||rd||inf/(1+||c||inf) <= opt_tol;
- mu/(1+|c^T x|+|b^T y|) <= gap_tol;
- |c^T x-b^T y|/(1+|c^T x|+|b^T y|) <= gap_tol;
- variable nonnegativity and dual slack nonnegativity within tolerance.

Report the raw residual vectors, their infinity norms, mu and absolute objective
gap as well as the normalized diagnostics. Reject nonfinite iterates as success.
Feasibility includes nonnegativity, not only Ax=b. Starting values must be
strictly positive; tolerance at termination does not relax initialization.

Defaults: feasibility/optimality/gap 1e-8, pivot 1e-12, tie_atol 1e-10,
tie_rtol 1e-9, relative rank factor 1e-12, sigma .5, fraction .99,
iteration budget 1000. All are configurable. Rank cutoff is
rank_tol*max(m,n)*largest_singular_value. Rank near the cutoff is uncertain,
not evidence of infeasibility; the width of an uncertainty band is not yet
specified. Tests pin the cutoff itself and exact dependence, not an invented band.

Ratio candidates satisfy |r_i-r_min| <= tie_atol +
tie_rtol*max(|r_i|,|r_min|). Apply Bland among candidates whose own ratio step
keeps all basic values feasible. The tests use feasibility allowance
feas_tol*(1+||x_B||inf) and explicitly reject a smaller-ID tied candidate whose
step makes another basic value negative beyond this allowance. A tiny positive
pivot cannot be ignored to falsely certify unboundedness. Return numerical
failure if a reliable pivot/certificate cannot be established.

For nonnegative x,s and exact equality feasibility, the objective gap equals
x^T s=n*mu. Consequently the normalized gap guard is stricter than normalized
average complementarity with the common tolerance when n>1. With residuals,
the two need not agree. Tests isolate both guards instead of assuming equality.

Assignment page 4 says both equality systems must be violated, then later says
at least one. Proposed: general solver accepts all strictly positive starts,
including feasible starts; assignment examples violate both, satisfying the
stricter wording. The user approved this choice. Current two-start fixtures
violate both systems. A separate test accepts a fully equality-feasible start.

## Assignment-to-test checklist

Paths link to test functions or files; these are coverage contracts, not passing
implementation claims. Small unit fixtures intentionally need not meet 8/5.

| Requirement / assignment page | Test coverage | Remaining evidence |
|---|---|---|
| Continuous original variables; 8 variables / 5 substantive constraints, p1 | [original size](tests/test_model.py), `test_assignment_size_uses_original_model`, `test_nonnegative_declarations_and_generated_rows_do_not_meet_assignment_size` | Construct actual submission models later; substantive modeling requires human judgment |
| Min c^T x, Ax=b, x>=0; correspondence, p1 | [conversion and recovery](tests/test_model.py) | Implement conversion after review |
| Reusable two-phase method, p2 | [simplex tests](tests/test_simplex.py) | All numerical routines pending |
| Basis inverse/basic values/reduced costs, p2 | `test_basis_inverse_basic_values_dual_and_reduced_costs`; [trace recomputation](tests/test_results.py) | Trace independent checks pending implementation |
| Bland entering and tied leaving original indices, p2 | `test_bland_enter_uses_smallest_eligible_original_index`, `test_bland_leave_tie_uses_variable_index_not_row`, cycling fixture | Pivot index persistence across multiple pivots needs further trace review |
| Negative RHS/artificial basis; Good/Bad/Ugly start, p2 | `test_phase_one_flips_negative_rhs_and_builds_identity_artificials`, `test_phase_one_reuses_feasible_unit_columns_and_adds_only_needed_artificials`, [lecture examples](tests/test_lecture_examples.py) | Phase I implementation pending |
| Lecture examples: degeneracy, cycling, Bland, artificial cleanup, p2 | [tests/test_lecture_examples.py](tests/test_lecture_examples.py) | Pivot sequences pinned only under Bland; other rules may differ |
| Positive Phase I sum; zero artificial cleanup; augmented dependence, pp2-3 | `test_phase_one_positive_sum_certifies_infeasibility`, `test_zero_basic_artificial_is_pivoted_out`, `test_removed_row_evidence_preserves_augmented_dependence`, inconsistent/zero-row tests | Numerical rank uncertainty tested separately |
| All iteration fields/termination reason, p3 | `test_simplex_trace_contains_both_phases_and_mathematically_consistent_basis` | Runtime reporting/driver later |
| Finite, unbounded, infeasible, dependent examples, p3 | [known optima and certificates](tests/test_simplex.py), [certificate checks](tests/test_results.py) | Four submission-sized models, printed recession-cone data, report proofs later |
| Full row rank IP input, p3 | `test_rank_deficient_ip_input_is_unsupported_not_infeasible`; [scaled rank/cutoff tests](tests/test_numerics.py) | Uncertainty-band width deferred until implementation design |
| Positive user starts; no feasibility solve, p4 | [initialization tests](tests/test_interior.py), `test_feasible_positive_start_is_accepted_by_general_api` | General API and stricter assignment examples distinguished |
| Centered primal-dual Newton system, p4 | `test_newton_direction_satisfies_all_three_block_equations`, `test_centering_target_is_sigma_times_average_not_affine_scaling` | Algorithm implementation pending |
| Positivity and steps, p4 | `test_fraction_to_boundary_is_capped_and_strictly_positive`, IP log tests; nonnegativity/ratio-feasibility tests | No algorithms implemented |
| Two distinct starts, same finite LP, p4 | `test_two_distinct_infeasible_starts_reach_same_known_optimum` | Submission-sized LP and comparisons later |
| Every x,y,s, objectives, residuals, mu,sigma,steps, p4 | `test_ip_logs_recompute_residuals_and_keep_every_iterate_interior` | Runtime reporting later |
| Joint stopping; limits/numerical failure distinct, pp3-4 | [status/failure tests](tests/test_results.py), [stopping and nonnegativity tests](tests/test_numerics.py) | All four normalized criteria tested; exact KKT reference and invalid sign cases |
| Stated feasibility/reduced-cost/pivot/tie/rank tolerances, p3 | Explicit-tolerance Bland tests; [options, scaling and rank tests](tests/test_numerics.py) | Numerical defaults approved; implementation pending |
| Commercial solver script/version/settings/status, p1 | Not covered by unit tests | Separate integration work; no verification claimed |
| Models, data, driver, report PDF, p2 | Not covered by this stage | Later deliverables |
| Searchable AI record and checked mathematics, pp1-2 | `ai_record/test_records.py`, decisions, verification log | Active export always has a saved-message cutoff |

## Fixture mathematics and provenance

Most fixtures below were constructed for these tests. The cycling coefficients
are section 8 of the course lecture notes (supplied after Phase 1). Other
lecture examples are not yet tests: see "Proposed changes" at the end. Their
numbers were recomputed independently.
The cycling model coefficients were checked against
[Cornell's simplex cycling example](https://people.orie.cornell.edu/miketodd/or630/SimplexCyclingExample.pdf).
This is an external reference, not the user's lecture notes.

- min -3x-2y with x+y<=4, x<=2, y<=3: optimum (2,2), value -10.
  The bound 3x+2y=2(x+y)+x<=10 proves optimality.
- min x+2y, x+y=3, nonnegative: x+2y=3+y>=3; optimum (3,0).
  Dual multiplier 1 and slacks (0,1) give equal primal/dual values 3.
- x-y=1, min -x-y: (1,0)+t(1,1) is feasible and value -1-2t.
- x=1 and 2x=3 contradict; x=1 and 2x=2 are dependent in [A|b].
- Newton fixture: x=s=(1,1), y=0, A=(1,1), b=3, c=(1,2), sigma=.5.
  rp=-1, rd=(0,-1), mu=1. dx=(1,0), dy=1.5, ds=(-1.5,-.5)
  satisfy all three block equations with centered RHS (-.5,-.5).
- Cycling coefficients: x=(1,0,1,0) attains max value 1. Multipliers
  (0,18,1) on the three <= rows bound the objective by 1 because
  A^T lambda=(10,-27,-9,18)>=(10,-57,-9,-24). This verifies the optimum
  independently of any pivot sequence; it does not prove that a particular
  non-Bland implementation cycles.

## Reproduction

```
python -m venv .venv
.venv/Scripts/python -m pip install -r requirements.txt
.venv/Scripts/python -m pytest -v --tb=short   # plain `pytest` also works via pytest.ini
python -m unittest discover -s ai_record -p "test_*.py" -v
```

Documentation tests need the existing reportlab/pypdf environment described in
ai_record/README.md. Full-suite execution should use an environment containing
both those existing documentation dependencies and NumPy/pytest. Do not count
documentation import/setup failures as intended solver failures.

## Proposed changes (APPLIED after your approval of A, B and C)

The proposal text is kept for provenance. What was actually implemented is in
"Applied changes" below, which also lists differences from the proposal.

Original note: nothing in this section had been changed in `tests/` when proposed. The lecture numbers below
were recomputed independently with NumPy (basis inverses, x_B, multipliers,
every reduced cost in notes sections 1, 5, 6, 8 and 9, plus a naive Dantzig run
and a naive Bland run). They matched the notes in every case. The notes use
1-based variable labels; tests would use 0-based indices.

### A. Replace two implementation-coupled tests

**Problem 1.** `test_linear_algebra_failure_maps_to_numerical_failure` and
`test_nonfinite_linear_algebra_output_cannot_be_success` monkeypatch
`np.linalg.inv` and `np.linalg.solve`, so they force the solver to call those
functions. The low-level contract (`basis_state` and `newton_direction` raise
`LinAlgError` on singular data) is already tested with real singular matrices
and stays.

Proposal: replace both with one property test over hard real inputs, run for
both methods, that constrains only the observable result:

```python
HARD = [  # (LP, start for interior)
    LP([-1], [[1e-14]], [1], ['<=']),                                     # tiny pivot
    LP([1e300, 2e300], [[1e300, 1e300]], [3e300], ['=']),                 # overflow scale
    LP([1e-300, 2e-300], [[1e-300, 1e-300]], [3e-300], ['=']),            # underflow scale
    LP([1, 1], [[1, 1], [1, 1 + 1e-13]], [1, 1], ['=', '=']),             # near-dependent rows
]

def test_hard_inputs_never_raise_or_fake_success(lp, method):
    result = solve(lp, method=method, start=...)    # must not raise LinAlgError
    assert result.status in {'optimal', 'numerical_failure', 'iteration_limit'}
    if result.status == 'optimal':
        # every array and the objective finite, and an independent check passes
        assert check_certificate(A_std, b_std, c_std, result, tolerance=1e-6)
    else:
        assert result.message
```

Trade-off: the exact mapping "LinAlgError becomes numerical_failure" is then not
proven by a test, because no input the solver admits produces a singular system
inside it (interior rejects rank-deficient A first; simplex removes dependent
rows). Alternative: add an injectable linear-solver option only for testing. I
recommend against it (extra API surface). The mapping would instead get a
focused unit test of the handler at implementation time. Your decision.

**Problem 2.** `test_uncertain_rank_is_numerical_failure_never_infeasibility`
requires `numerical_failure` for `diag([1, 2e-12])`. No approved rule says that,
and it also forces simplex to fail there. Proposal, using known mathematics:

```python
# min x1 + x2, diag(1, 2e-12) x = (1, 2e-12): unique feasible x = (1, 1), value 2.
def test_nearly_dependent_but_feasible_never_reports_infeasible(method):
    result = solve(LP([1, 1], np.diag([1., 2e-12]), [1., 2e-12], ['=', '=']), method, start=...)
    assert result.status in {'optimal', 'numerical_failure'}
    if result.status == 'optimal':
        # x close to (1, 1), objective close to 2, certificate checks pass

# rows (1,1) and (1,1+1e-13), rhs (1,2): needs x2 = 1e13 and x1 = -1e13, so truly infeasible.
def test_nearly_dependent_infeasible_is_never_optimal(method):
    assert solve(...).status in {'infeasible', 'numerical_failure'}
```

This pins correctness without prescribing which status a borderline matrix
gets. `rank_diagnostics` keeps its direct tests (exact dyadic cutoff case, exact
dependence, scale invariance), so the 'uncertain' label itself stays tested.

### B. Lecture-note examples to add

| Example (notes section) | Test would assert |
|---|---|
| s1.2-1.3: A=[[1,1,1,0],[2,1,0,1]], b=(4,5) | basis (3,1): B^-1=[[1,-1/2],[0,1/2]], x_B=(3/2,5/2). Basis (1,4): x_B=(4,-3), reported as an infeasible basic solution, not an error |
| s5 bounded: max 3x1+2x2, x1+x2<=4, 2x1+x2<=5 | bases (3,4), (3,1), (2,1): x_B=(4,5), (3/2,5/2), (3,1); multipliers (0,0), (0,-3/2), (-1,-1); c_bar2=-1/2 and c_bar4=3/2 at (3,1); optimum (1,3), min value -9 (profit 9); final c_bar3=c_bar4=1 |
| s6 unbounded: min -x1-x2, x1-x2<=1 | status unbounded; standard_x=(1,0,0), ray=(1,1,0), A d=0, c.d=-2. s6.3: same constraints with min x1+x2 is optimal at (0,0), value 0 |
| s7.2 degenerate: min -x1, x1+x2=0 | optimal (0,0); one zero-length pivot; final c_bar2=1 |
| s8-9 cycling | `to_standard` of the max form reproduces the notes' A, b, c exactly (slacks are columns 5-7). Bland from basis (5,6,7) visits (5,6,7), (1,6,7), (1,2,7), (3,2,7), (3,4,7), (5,4,7), (5,1,7), (5,1,3); six zero steps, then step 1; final x=(1,0,1,0,2,0,0), c.x=-1, c_bar=(30,42,18,1) for x2,x4,x6,x7. Low level: at basis (5,4,7) reduced costs (-22,93,21,-24) make `bland_enter` choose x1, not x6; with u=(-4,1/2,1) and x_B=(0,0,1), `bland_leave` picks x4 with step 0. Section 9.1: basis (8,2,5) with rows 1 and 2 tied leaves x2 |
| Slides "Good": min -x1-2x2, x1+x2<=4, -x1+2x2<=2 | optimum (2,2), value -6; no Phase I rows in the trace (see C) |
| Slides "Bad": min 2x1+3x2, x1+x2>=2, x1+2x2=3, 2x1+x2<=6 | `to_standard` gives A=[[1,1,-1,0],[1,2,0,0],[2,1,0,1]], b=(2,3,6); `phase_one` adds artificials to rows 1 and 2 only, basis (x5a,x6a,x4); optimum (1,1), value 5 |
| Slides "Ugly": x1+x2+x3=4, x1+2x2+3x3=7, 2x1+3x2+4x3=11, min x1+2x2+3x3 | rank 2 because row3=row1+row2 and b3=b1+b2: optimal with value 7 (every feasible point attains it); one removed row with weights proportional to (1,1,-1). With b3=12 it is infeasible. Interior rejects it (ValueError); `rank_diagnostics` returns deficient |

Cycling data (notes section 8): A=[[1/2,-11/2,-5/2,9,1,0,0],
[1/2,-3/2,-1/2,1,0,1,0],[1,0,0,0,0,0,1]], b=(0,0,1), c=(-10,57,9,24,0,0,0).
The existing cycling test already uses these coefficients in max form.

### C. Decision needed: when does Phase I add artificials?

The slides' "Good" case says Phase I is not needed when the identity is already
in A, and the "Bad" case adds artificials only to rows lacking a unit column.
The current `test_phase_one_flips_negative_rhs_and_builds_identity_artificials`
uses a matrix with no unit columns, so it holds either way. But the lecture
traces (s5, s6, s7.2, s8-9 all start from the slack basis) can only be asserted
if the solver reuses existing unit columns and skips Phase I when the identity
is present.

Recommendation: follow the lectures (reuse unit columns; skip Phase I when all m
are present; the Phase I/II trace test for x1+x2=3 stays). Alternative: always
add m artificials and assert only final answers for the lecture examples.
Status: pending your choice.

## Applied changes (after your approval)

- **Phase I contract (C):** `phase_one` flips rows with negative RHS, reuses the
  largest-index column exactly equal to e_i for each row, appends artificials in row
  order only where no such column exists, and reports them in `PhaseState.artificial`
  (new field). If none are needed a feasible identity basis exists and Phase I is
  skipped: the artificial-sum objective would have nothing to minimize. Tests:
  `test_phase_one_reuses_feasible_unit_columns_and_adds_only_needed_artificials`
  (negative RHS that becomes a slack, the negative-RHS trap, duplicate unit columns,
  zero RHS, Good/Bad/Ugly slides, dependent rows), plus solve-level tests in
  `tests/test_lecture_examples.py`.
- **Tie rule (new, my choice, not in the proposal):** when two columns equal e_i the
  largest index is used. The notes' section 7.2 example (`x1+x2=0`) has two such
  columns and starts from x2; a smallest-index rule would never pivot there.
  Slacks follow structural columns, so the largest index also prefers a slack. Say if you want a different rule.
- **Numerical tests (A):** the three coupled tests are gone. New tests
  `test_hard_inputs_never_fake_success` (tiny pivot, 1e200 and 1e-200 scale,
  near-dependent rows, both methods), `test_nearly_dependent_but_feasible_never_reports_infeasible`
  and `test_nearly_dependent_infeasible_is_never_optimal` use a scale-aware independent
  KKT check (not `check_certificate`) on any returned optimum and known expected
  answers. Interior may reject near-dependent rows as unsupported input (ValueError);
  simplex may not raise. The infeasible case is infeasible by a normalized margin
  near .3, over 1e7 times feas_tol.
- **Lecture examples (B):** `tests/test_lecture_examples.py` (31 cases): notes
  sections 1 and 5 bookkeeping and bounded example, 6 unbounded and bounded-objective
  cases, 7.2 degeneracy, 8-9 cycling data, Bland leave/enter ties, Good/Bad/Ugly,
  artificial cleanup, dependent rows and negative RHS. Pivot sequences are pinned
  only under Bland and labelled as such; section 5 and the first five cycling pivots
  coincide with the notes' Dantzig run, and the divergence at basis (5,4,7) is tested
  at the `bland_enter` level. Rule-independent end results are asserted separately.
- **Not covered:** a Dantzig run that cycles cannot be tested because only Bland's
  rule is exposed; the notes' cycle is covered by its data, Bland's escape and the
  low-level choices.
- **Reference for expected values:** hand algebra, a scratch NumPy replay of the
  notes' pivots, and vertex enumeration for the optima. No solver was written.
