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

## Template for future entries (not an actual decision)

- ID / date / tool / session ID / transcript source line:
- Suggestion and context:
- Status: proposed / accepted / rejected / corrected
- Decision maker and reason:
- Actual implementation or correction (file/commit if applicable):
- Verification: independent calculation or exact command, observed result, evidence path; otherwise `not yet verified`.
