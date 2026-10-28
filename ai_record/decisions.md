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
- Status: proposed; no track chosen and no solver implementation authorized in this stage.
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
- Status: pending user clarification of expanded scope or instructor confirmation; no solver development started and no approval invented.
- Why: implementing both methods adds work without a documented extra-credit benefit.
- Verification: rechecked the actual assignment text during this closeout; no mathematical calculation is involved.

## Template for future entries (not an actual decision)

- ID / date / tool / session ID / transcript source line:
- Suggestion and context:
- Status: proposed / accepted / rejected / corrected
- Decision maker and reason:
- Actual implementation or correction (file/commit if applicable):
- Verification: independent calculation or exact command, observed result, evidence path; otherwise `not yet verified`.
