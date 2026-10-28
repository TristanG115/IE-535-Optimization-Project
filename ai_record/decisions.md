# Important AI suggestions and decisions

Record only consequential suggestions actually discussed. `proposed` is not user acceptance. Accepted, rejected and corrected entries should say who made that decision and why. Link to the session ID and transcript source line; append later verification rather than rewriting history.

## D001 - Preserve originals with readable derivatives

- Date: 2026-10-27
- Session: Codex `01a17ff8-0eac-7342-a76a-d9bf68abcde3` (documentation setup; see sessions.csv).
- Suggestion: retain byte-for-byte exports with SHA-256 hashes and derive readable transcripts for searching and PDF compilation.
- Status: implemented by Codex within the user's requested documentation setup; user review pending.
- Why: preserves actual evidence while making prompts, responses and available reasoning summaries easy to read. A shortened transcript alone is not the full source export.
- Verification: all four documentation tests passed; a real Codex snapshot preserved its original hash, compiled to a three-page searchable PDF, and all rendered pages were inspected. See verification.md for commands and limitations.

## D002 - Confirm one-track versus both-track scope

- Date: 2026-10-27
- Session: same Codex documentation session.
- Suggestion: confirm submission scope before solver implementation. The assignment (page 1) asks students to choose one of two tracks; the user mentioned implementing both.
- Status: corrected by the user on 2026-10-27. Both tracks are chosen for this project; solver implementation has not begun.
- Why: implementing both increases work beyond the stated assignment requirement.
- Verification: checked against pages 1-4 of the supplied assignment; this is a scope observation, not a mathematical result.

## D003 - Require documentation closeout for every session

- Date: 2026-10-27
- Session: Codex `01a17ff8-0eac-7342-a76a-d9bf68abcde3`; follow-up user request to make closeout mandatory.
- Decision: the user explicitly requested end-of-session conversation preservation, tracker updates, meaningful decision records, pending approval labels, a short summary and a local commit. Add `CLAUDE.md` pointing to the shared `AGENTS.md` rules.
- Status: accepted by explicit user instruction; implemented in AGENTS.md and CLAUDE.md.
- Why: apply the same documentation discipline in future Codex and Claude work without duplicated rule sets.
- Export limitation: a live capture cannot include a final reply that has not yet been saved. Record the actual cutoff, preserve everything available, and refresh the saved ending at the next opportunity; never reconstruct it.
- Verification: all four documentation tests passed during this closeout; `git diff --check` reported no whitespace errors. Read AGENTS.md and CLAUDE.md to confirm the shared rules and explicit snapshot limitation. The tracker records the new export's actual cutoff.

## D004 - Extra-credit expectation conflicts with assignment

- Date: 2026-10-27
- Session: same Codex follow-up, including the user's existing AGENTS.md edit stating a preference for both solvers to obtain extra credit.
- Recommendation: preserve that preference, but do not assume it earns extra credit. The supplied assignment's first page explicitly says there is no extra credit.
- Status: superseded by the user's 2026-10-27 correction. The user chose both methods and reported the professor's in-class extra-credit confirmation. No solver development has begun.
- Why: implementing both methods adds work without a documented extra-credit benefit.
- Verification: rechecked the actual assignment text during this closeout; no mathematical calculation is involved.
- Later user correction: the professor confirmed in class that both methods earn extra credit. This is user-reported instructor guidance, not independently verified instructor evidence. The project scope is both options; the written-policy conflict is recorded rather than treated as a pending choice.

## D005 - One current transcript per continued session, including its saved final reply

- Date: 2026-10-27
- Session: Codex `01a17ff8-0eac-7342-a76a-d9bf68abcde3`; user follow-up about the two overlapping transcript files.
- Decision: explicitly requested by the user. Replace the previous session transcript/export and tracker row with the entire actual saved conversation as it continues; retain earlier revisions in Git instead of accumulating overlapping current files.
- Status: accepted by user instruction and implemented. No mathematical or architectural approval is being inferred.
- Correction: prior closeouts preserved snapshots but omitted replies written after capture. A final-reply watcher now waits for the actual saved assistant final message, exports it and locally commits only that session's records. Starting the watcher is pending capture, not proof of completion.
- Verification: seven documentation tests passed, including session replacement, refusal to discard older Codex history, timeout without fabricated content, and a real temporary Git commit containing a synthetic saved final reply. Real-session consolidation and the finalizer's actual status are recorded in verification.md and process logs.

## D006 - Readable PDF focuses on the conversation

- Date: 2026-10-27.
- Decision maker: user, in this request and the interactive option selection.
- Choice: keep every actual user prompt and saved assistant response with dates and times; use brief contextual research and tool notes beside the relevant exchange. The user selected this option over a separate appendix or full tool output. Preserve original raw logs unchanged.
- Reason stated by user: the current PDF contains too much system, permission and skill material and is hard to read. The user did not give a separate reason for selecting inline notes; the recommendation was that they keep evidence in context without overwhelming the conversation.
- Status: accepted; exporter and S001 regeneration pending final review before commit.
- Verification: ten documentation tests passed; the regenerated six-page S001 PDF was text-checked and visually inspected. See verification.md.

## D007 - Interactive choice for meaningful design decisions

- Date: 2026-10-27.
- Decision maker: user, by explicit request.
- Choice: present a few options, a recommendation and tradeoffs through `request_user_input` when available, or ask in chat. Record accepted, rejected or modified choices and the user's stated reasons. Do not decide meaningful design questions for the user; routine implementation details need no approval.
- Status: accepted; recorded in AGENTS.md for future sessions.
- Reason stated by user: they want to select an option or provide their own reasoning.
- Verification: AGENTS.md was reviewed and the documentation suite passed after this rule was added.

## D008 - Both project options and professor's extra-credit correction

- Date: 2026-10-27.
- Decision maker: user, reporting an in-class statement by the professor.
- Choice: implement both project options. The user says the professor confirmed extra credit for both, despite the original assignment PDF saying otherwise.
- Status: user correction recorded; no algorithm implementation authorized in this stage.
- Reason stated by user: the professor's in-class confirmation.
- Verification: the written assignment's conflicting statement remains preserved in attachments; the professor's statement is user-reported and not independently verified.

## D009 - Phase 1 scope and shared interface

- Date: 2026-10-27 (America/Indianapolis).
- Session: Codex `01a18013-3e63-7f12-ac5c-286df8aeb180`; see its current transcript and raw source. User request begins at raw line 16; interactive choices follow in that same session.
- Recommendation: one lp_solver.py module with dataclasses and testable numerical functions, rather than a multi-module package or dictionaries; pytest and NumPy only for solver work.
- Status: accepted by the user's interactive selection. The user did not give a separate reason for choosing the interface. The recommendation's rationale was simplicity and intermediate-calculation testability.
- User scope: create failing tests and minimal stubs, update AI records, then stop for review. No solver implementation, commit or push is authorized yet. This supersedes the earlier documentation-only scope, without authorizing algorithm implementation.
- Verification: 152 new tests collected and failed explicitly for missing functionality, not imports. Existing 10 documentation tests passed in the full pytest run. No numerical algorithm is implemented.

## D010 - Assignment-aligned algorithms and initialization policy

- Date/session: same Phase 1 session; actual interactive replies retained in raw export and transcript.
- Recommendation: explicit basis-inverse Two-Phase Simplex with Bland entering/leaving rules; centered infeasible-start primal-dual IP with fixed configurable sigma and separate primal/dual fraction-to-boundary steps. IP requires full-row-rank standard form, without general infeasible/unbounded certification promises.
- Status: accepted by interactive selection. No separate reason was supplied for choosing these algorithm contracts. These match the assignment's requested calculations while avoiding unsupported status claims.
- Initialization correction: assignment page 4 first asks for both equality systems to be violated, then says at least one. User selected the general API accepting all finite strictly positive x,s with finite y, including feasible starts; assignment-example fixtures violate both equalities. Reason offered in recommendation: valid general starting points should remain admissible while the assignment examples satisfy the stricter wording. The user gave no additional reason.
- Verification: literal Newton block equations and first update checked using exact Fraction arithmetic; two-start and feasible-start tests exist but deliberately fail at stubs. Lecture notes were not supplied; no fixture is represented as a user lecture example.

## D011 - Scaled numerical stopping contract, modified by the user

- Date/session: same Phase 1 session; user requested exact formulas before choosing, then approved the numerical contract with four modifications and later approved the precise extension.
- Original recommendation: rp=Ax-b, rd=A^T y+s-c; normalize infinity residuals by 1+||b||inf and 1+||c||inf. Normalize mu=x^T s/n by D=1+|c^T x|+|b^T y|. Require all three thresholds, distinguishing numerical failure and iteration limit from success/infeasibility.
- User modifications: combine absolute and relative ratio ties; add |c^T x-b^T y|/D as an explicit fourth stopping check; report raw and normalized diagnostics; account for numerical scaling. Treat uncertain rank as numerical uncertainty, not infeasibility.
- Status: accepted as modified by the user. Defaults approved: feas_tol=opt_tol=gap_tol=1e-8, pivot_tol=1e-12, tie_atol=1e-10, tie_rtol=1e-9, rank_tol=1e-12, sigma=.5, fraction=.99, max_iter=1000. All remain configurable. Relative rank cutoff is rank_tol*max(m,n)*largest singular value.
- Reason stated by user: explain and verify stopping criteria, account for varying coefficient scales, preserve Bland's rule and feasible pivots. The recommendation additionally explained that complementarity alone cannot establish optimality. Exact feasible primal/dual data satisfy objective gap=n*mu; with equality residuals these quantities need not coincide.
- Verification: raw/normalized literal diagnostics, separate guard isolation, configurable/inclusive thresholds, positive row scaling, rank scale invariance and cutoff uncertainty tests were added. All remain intentionally red. The uncertainty-band width and broader conditioning policy remain unspecified for the later implementation discussion; no numerical theorem is inferred from a tolerance choice.

## D012 - Nonnegativity and feasible ratio ties

- Date/session: same Phase 1 session; user's explicit final follow-up at raw line 158, plus preceding interactive approval.
- Approved rule: |r_i-r_min| <= tie_atol+tie_rtol*max(|r_i|,|r_min|). Choose the smallest original basic-variable ID among tied candidates whose ratio step preserves basic feasibility within scaled tolerance.
- User clarification: feasibility must explicitly include variable nonnegativity as well as Ax=b; a leaving variable must not produce a basic solution infeasible beyond tolerance.
- Status: accepted by explicit user approval and clarification. Reason stated: prevent infeasible resulting basic solutions; make nonnegativity explicit.
- Verification: exact/absolute/large-scale relative ties, a smaller-ID candidate rejected for creating a negative basic value beyond tolerance, negative primal/dual slacks despite zero residuals/gap, configurable nonnegativity tolerance, and certificate corruption tests added. A tiny positive pivot may lead to a reliable optimum or numerical failure, but must not falsely certify unboundedness. No algorithm was implemented to make these tests pass.

## D013 - Commit and push after major steps and completion

- Date: 2026-10-27; continued Codex session `01a18013-3e63-7f12-ac5c-286df8aeb180`.
- Decision maker: user, by explicit request to add this workflow to AGENTS.md.
- Choice/status: accepted. Require a clear commit after each major verified step and at completion when changes remain, followed by a push to the configured remote. This provides standing push authorization for those checkpoints; explicit review holds still take precedence. Include the final saved-reply record commit in the push workflow after capture succeeds.
- Reason: the user gave no separate reason for the change.
- Current boundary: this request changes the standing instructions; it does not explicitly approve the pending Phase 1 results. Their existing pre-commit review hold remains in effect. No commit or push is made in this follow-up. `git remote -v` returned no remotes, so a future push also requires a destination to be configured.
- Verification: reviewed both the checkpoint rule and closeout step 4 for consistency. Documentation test and whitespace-check results are recorded in verification.md. No mathematical or algorithm choice changed.

## D014 - Claude Code review of the Phase 1 tests: five corrections

- Date: 2026-10-27. Tool/session: Claude Code, session `1be70a1c-9624-43ca-8083-418f0621d4b9` (its own record; the Phase 1 Codex session and raw logs were not edited).
- Request: the user asked Claude to review the Phase 1 prompt/results and correct anything wrong.
- Status: five corrections applied by Claude within the review request; they remain uncommitted for the user's review. The user has not yet said whether they accept each one.
- Corrections, why, and verification (all verified by `python -m pytest -q`: 152 failed, 0 errors before and after, with both `pytest` and `python -m pytest`):
  1. Bare `pytest` failed with 5 collection ImportErrors (`lp_solver` not importable); only `python -m pytest` worked, contradicting "0 setup errors". Added `pytest.ini` (`testpaths = tests`, `pythonpath = .`). Verified by running both commands.
  2. The assignment-size fixtures used singleton rows (`x_i <= 1`), which are bounds in disguise and conflicted with the rule that bounds are not substantive constraints. Replaced with distinct multi-variable rows. Verified by reading the three size cases (8/5 eligible, 7/5 and 8/4 not).
  3. The empty-objective validation case also had mismatched `A`, so it was rejected for the wrong reason. Now `c=[]` with a consistent empty `A`, `b`, `relations`. The test count stays 152.
  4. The rank-cutoff test relied on `1e-12*2*sigma_max == 2e-12` surviving an SVD exactly. Now `diag([1, .5])` with `rank_tol=.25` (cutoff .25*2*1 = .5, exact in binary).
  5. Cycling-test name. Claude renamed it to say "not Beale's 1955 example" from memory, with no source. The lecture notes (section 8) later supplied by the user call these exact coefficients the classical Beale example, so Claude withdrew that claim. The test is now `test_blands_rule_escapes_course_cycling_example`. This is a correction of Claude's own earlier correction.
- Independent mathematics checked while reviewing: every fixture value in the five test files (Newton step, first centered update, reduced costs, ratio ties, standard-form conversions, size/diagnostic formulas, cycling bound with multipliers (0,18,1)) by hand; lecture-note values recomputed with NumPy (see D015). No solver code was written.

## D015 - Proposed test changes and lecture-note examples (pending the user)

- Date/session: same Claude Code session `1be70a1c-9624-43ca-8083-418f0621d4b9`.
- User input: the user agreed they do not want tests that force a specific NumPy call or assume every nearly singular matrix is a `numerical_failure`, asked for precise implementation-independent replacements before any change, and supplied the course simplex slides and lecture notes.
- Claude's proposals (recorded in PHASE1.md, "Proposed changes"; no test was changed): (A) replace the two `np.linalg` monkeypatch tests with a property test over hard real inputs (tiny pivot, 1e300/1e-300 scale, near-dependent rows) that requires no exception and either a non-success status or a finite, independently certified optimum; replace the uncertain-rank solver test with two known-answer near-dependent cases that accept `optimal`/`numerical_failure` (feasible) or `infeasible`/`numerical_failure` (infeasible) but never a wrong answer. (B) add lecture examples (sections 1, 5, 6, 7.2, 8-9 and the Good/Bad/Ugly slides). (C) decide when Phase I adds artificials: Claude recommends following the lectures (reuse existing unit columns, skip Phase I when the identity is present).
- Status: PENDING the user's approval of A, B and C; trade-off for A recorded (the LinAlgError-to-numerical_failure mapping would not be directly tested through real inputs).
- Verification: every lecture number used in B (basis inverses, x_B, multipliers, all reduced costs in sections 1, 5, 6, 8, 9, the full cycling and Bland pivot sequences, Good/Bad/Ugly optima by vertex enumeration) was recomputed with NumPy; all matched the notes. This verifies the notes' arithmetic, not any solver.

## D016 - Approved: implementation-independent numerical tests, lecture examples, Good/Bad/Ugly Phase I

- Date/session: 2026-10-27, Claude Code session `1be70a1c-9624-43ca-8083-418f0621d4b9`; resolves the pending parts of D015.
- User decision (explicit): approved proposals A (replace the two NumPy-coupled tests and the uncertain-rank test), B (add the lecture examples) and C (follow the professor's Good/Bad/Ugly approach: reuse an existing feasible identity basis, add artificials only where needed, skip Phase I when a valid start exists and document why). Stated reasons: tests must not force a particular NumPy implementation or classify every nearly singular matrix as a failure; any returned optimum must be independently verified; infeasible examples must be clearly infeasible relative to tolerances; the work must handle negative RHS and dependent constraints; different pivot rules may give different iteration sequences.
- Applied by Claude: Phase I contract and `PhaseState.artificial` field (stub only); new property/known-answer numerical tests; `tests/test_lecture_examples.py`; the old coupled tests removed. Details and differences from the proposal are in PHASE1.md "Applied changes".
- Claude's own choice, **accepted by the user on 2026-10-28** ("all changes and proposed ideas look good"; no separate reason given): when several columns equal the same e_i, use the largest index (slacks follow structural columns). Reason: notes section 7.2's `x1+x2=0` starts from x2; smallest-index would never pivot and the lecture trace could not be tested. Alternative: smallest index, or require the caller to supply the basis.
- Also decided by Claude, **accepted by the user on 2026-10-28** (no separate reason given): interior may reject near-dependent rows as unsupported input (ValueError) in the new tests, while simplex may not raise; unit-column detection is exact equality, with no tolerance, so an approximate unit column is never treated as identity.
- Verification: `python -m pytest ai_record tests`: 197 failed (all NotImplementedError, checked from JUnit XML), 10 documentation tests passed, 0 errors/skips; plain `pytest` also collects cleanly. Expected values were checked independently without a solver: Good (2,2) -6, Bad (1,1) 5, Ugly 7 (every feasible point), dependent-rows LP 4 at (1,0,3), negative-RHS LP -4 at (4,0), full cycling/Bland pivot sequence replayed with a scratch NumPy script (cycle under Dantzig; Bland ends at basis (5,1,3), x=(1,0,1,0,2,0,0), value -1), and hand algebra for the bland_leave/enter cases and the near-dependent examples. This verifies the tests' expectations, not any solver.

## D017 - Approval of the Phase 1 review results; commit and push

- Date/session: 2026-10-28, Claude Code session `1be70a1c-9624-43ca-8083-418f0621d4b9`.
- User decision (explicit): approved all Phase 1 changes and proposals (D014-D016, including the largest-index unit-column tie rule and the interior-may-reject/simplex-may-not-raise convention), and asked to log them, commit and push. This lifts the pre-commit review hold for this Phase 1 work. No reason beyond approval was given.
- Outcome: see verification.md for the commit and push result. Solver implementation is still not authorized; it needs a separate go-ahead.
- Verification: same test run as D016 repeated before committing.

## Template for future entries (not an actual decision)

- ID / date / tool / session ID / transcript source line:
- Suggestion and context:
- Status: proposed / accepted / rejected / corrected
- Decision maker and reason:
- Actual implementation or correction (file/commit if applicable):
- Verification: independent calculation or exact command, observed result, evidence path; otherwise `not yet verified`.
