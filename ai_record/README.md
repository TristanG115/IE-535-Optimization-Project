# AI usage records

Start here before the next project conversation. Keep **all project prompts**, follow-ups, instructions supplied to agents, and corresponding responses or available session exports. Keep code blocks intact. Log important suggestions in `decisions.md` with reasons and actual verification. Missing history must be marked missing, never reconstructed.

The supplied assignment, pages 1-2, requires a searchable AI-record PDF organized by tool and conversation. It also makes the student responsible for all mathematical claims. These are reference requirements; they do not authorize solver implementation. The assignment asks for one track; confirm the intended scope before developing both.

## Files

- `sessions.csv`: one current row per tool/session ID. Re-exporting a continued session replaces that row and its files. Capture dates use UTC; assignment/project dates use America/Indianapolis.
- `raw/{codex,chatgpt,claude}/`: latest original export, unchanged, named by session ID. The tracker stores its SHA-256. Refresh only from actual source files; earlier versions remain in Git.
- `transcripts/{codex,chatgpt,claude}/`: readable text derived from actual records. Codex labels cite raw JSONL line numbers. Keep originals alongside these derivatives.
- `decisions.md`: accepted, rejected, corrected or still-proposed suggestions. No fabricated decisions or disagreements.
- `attachments/`: actual referenced input files; the supplied assignment is preserved here unchanged.
- `records.py`, `test_records.py`: one utility and one test file; unrelated to either solver.
- `compiled/`: generated combined Markdown and optional searchable PDF. Git ignores these reproducible files; keep source exports tracked. Retain the final submitted PDF separately when ready.

## Python on this computer

Python is not currently on the working shell's PATH. This bundled runtime was found and used successfully:

```powershell
$py = "$env:USERPROFILE\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
& $py --version
```

Run commands from the project root. On a normal Python installation replace `& $py` with `python`. Export and Markdown compilation use only Python's standard library. PDF generation needs `reportlab`; PDF tests also need `pypdf`. Both are installed in the runtime above. On another installation:

```powershell
python -m pip install reportlab pypdf
```

PDF rendering currently uses Windows Consolas (`C:\Windows\Fonts\consola.ttf`). Adapt the font path for other operating systems. Check unusual Unicode symbols visually before submission.

## Codex: actual saved data, concise reading copy

```powershell
& $py ai_record/records.py list
& $py ai_record/records.py codex "C:\full\path\to\rollout-session.jsonl" --topic "Documentation setup"
```

`list` reads session metadata and shows only sessions whose recorded workspace matches this project. Select the actual session; it does not guess the latest session. The current documentation conversation is `01a17ff8-0eac-7342-a76a-d9bf68abcde3`:

```powershell
& $py ai_record/records.py codex "$env:USERPROFILE\.codex\sessions\2026\10\27\rollout-2026-10-27T20-45-25-01a17ff8-0eac-7342-a76a-d9bf68abcde3.jsonl" --topic "Documentation setup"
```

Re-running this command replaces that session's export and transcript with the full saved conversation. Old hash-named snapshots and duplicate tracker rows are consolidated automatically, after checking their original hashes and verifying that the new Codex source extends every earlier source. A shorter or divergent Codex export is rejected; it cannot erase earlier messages. Do not concatenate overlapping transcripts.

To include the final reply itself, the agent starts this command in a **hidden background process before sending the final reply**, after committing verified implementation changes:

```powershell
& $py ai_record/records.py codex "C:\full\path\to\rollout-session.jsonl" --topic "Session closeout" --wait-final --commit
```

`--wait-final` watches only for a newly saved assistant final message after startup. It then exports the actual source and locally commits only that session's evidence and the tracker. It does not push or include unrelated staged changes. The default timeout is 180 seconds (`--timeout` changes it). A timeout leaves existing records unchanged and reports an error; inspect the process log and retry as needed. Launch with Windows `Start-Process -WindowStyle Hidden`, redirect stdout/stderr to ignored `tmp/` logs, and confirm the process is running before replying. A running watcher is pending, not a successful capture. Finalizer exit/log status should be checked at the next opportunity.

A normal export during active work remains a snapshot. Its cutoff is recorded automatically. Native exports are never reconstructed, and an incomplete JSON line causes a clear error instead of registration.

The original JSONL is the evidence. The Markdown copy preserves prompts and responses verbatim, in source order, and includes **available reasoning summaries only**. It excludes duplicated event mirrors, system/developer context, tool calls/results and encrypted data from the reading copy. Those remain in the raw original. Non-text content is marked; keep actual input files separately. The script supports observed message records and event-only logs. If formats change, review the raw source and adapt tests before trusting a new export. A supported mixed log uses response-item messages as the authoritative conversation stream.

This local file format and path were verified on this computer, not promised as a permanent public export API. `history.jsonl` alone is not the evidence source used here. [Official OpenAI configuration reference](https://learn.chatgpt.com/docs/config-file/config-reference) describes history and reasoning-display settings; it does not guarantee a complete conversation export or recovery of hidden reasoning. Do not change global Codex settings for this workflow.

If a session is absent, check the appropriate Codex home or archived directory with `list --sessions-dir "..."`, or retain an actual product export/full visible transcript. Record the gap in the CSV notes. Never create an AI-written substitute. This tool does not search other workspaces automatically, merge forks, or certify completeness.

## ChatGPT and Claude

Keep an actual native export when available. Save only the relevant project's full conversation, including prompts and replies, as UTF-8 `.txt` or `.md` for reading. A full visible copy is acceptable as a manually captured source when no native export is available; say so in CSV notes. Include visible reasoning summaries if present; do not ask a model to regenerate prior text or hidden thinking. Do not import a summary as a full transcript.

```powershell
& $py ai_record/records.py add chatgpt "C:\exports\project-chat.txt" --session-id "2026-10-28-chatgpt-01" --topic "Model review" --model "exact displayed name"
& $py ai_record/records.py add claude "C:\exports\original-export.json" --transcript "C:\exports\full-project-conversation.txt" --session-id "2026-10-28-claude-01" --topic "Test review"
```

Use the real conversation ID if available; otherwise a unique dated label. Leave model unspecified if unknown. These are command examples, **not existing conversations**. Native JSON/ZIP/HTML/PDF formats are preserved without speculative parsing; `--transcript` must contain the actual complete conversation text. Check that reading copy against its original manually and record verification in CSV notes. Keep referenced attachments with the raw export. No ChatGPT or Claude sessions have been fabricated or imported in this setup.

## After every meaningful session

1. Refresh the actual conversation and confirm its single row and stable session filename. Start the final-reply watcher before ending the turn.
2. Review the first/last messages, all prompts, follow-ups and attachments against the source. Edit `completeness` to `reviewed complete through <last message/time>` only when justified; otherwise retain snapshot/gap status. Store source/capture limitations in `notes`.
3. Add only meaningful suggestions to `decisions.md`. State the actual decision maker, why, what changed, and how it was verified. Pending review stays pending. For mathematics, retain independent checks; tests alone do not establish a theorem.
4. Commit the verified development stage with its records. Never push without authorization.

## Searchable PDF, now or later

```powershell
& $py ai_record/records.py bundle --pdf
& $py -m unittest discover -s ai_record -p "test_*.py" -v
```

Open `ai_record/compiled/ai_record.pdf` and search for a known prompt. The PDF includes the CSV index, decision log and one current reading copy per tool/session, ordered by tool and session. It checks raw hashes and regenerates Codex text to reject altered derivatives. Manual external-tool reading copies still require human source comparison. Generated files are text, not screenshots; raw tool details and attachments remain separate evidence. Recompile after the final-reply capture when a current PDF is needed; the finalizer updates source records only.

Before submitting, re-export ended conversations, inspect every CSV row for missing content, check the PDF's first/last messages and special symbols, and compile again. A successful PDF build does not prove all project conversations were captured.
