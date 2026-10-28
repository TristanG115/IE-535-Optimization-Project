"""Preserve real AI exports and compile readable, searchable records. No solver code."""
import argparse
import csv
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time
from xml.sax.saxutils import escape

FIELDS = "captured_utc tool model session_id topic raw_path transcript_path sha256 completeness notes".split()


def read_codex(data):
    records = []
    for number, line in enumerate(data.decode("utf-8-sig").splitlines(), 1):
        if not line.strip():
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError as error:
            raise ValueError(f"Invalid JSON at source line {number}; retry after the session writer finishes") from error
        if not isinstance(record, dict):
            raise ValueError(f"Invalid record at source line {number}")
        records.append((number, record))
    return records


def codex_transcript(data):
    records = read_codex(data)
    meta = next((r.get("payload", {}) for _, r in records if r.get("type") == "session_meta"), {})
    session_id = meta.get("id") or meta.get("session_id")
    if not session_id:
        raise ValueError("Missing Codex session ID; provide a real session export")
    models = sorted({r["payload"]["model"] for _, r in records if r.get("type") == "turn_context" and r.get("payload", {}).get("model")})
    use_messages = any(r.get("type") == "response_item" and r.get("payload", {}).get("type") == "message" and r["payload"].get("role") in ("user", "assistant") for _, r in records)
    parts = [
        f"# Codex session {session_id}",
        "Readable copy of saved prompts and assistant responses. Times are saved UTC timestamps; raw source lines identify the original record. The raw JSONL remains the complete evidence.",
        "Only saved text and available reasoning summaries appear here. Missing or unsaved content is not reconstructed.",
    ]
    count = 0
    exchange = 0
    tool_calls = {}

    def text_blocks(value):
        return [block["text"] if isinstance(block.get("text"), str)
                else f"[Non-text content: {block.get('type', 'unknown')}; see raw export and original attachment]"
                for block in value if isinstance(block, dict)]

    def readable_prompt(value):
        stripped = value.strip()
        if stripped.startswith(("<environment_context>", "<external_codex_apps_open_page>")):
            return None
        if "## My request:" in value and stripped.startswith(("# Context from my IDE setup:", "# Files mentioned by the user:")):
            return value.split("## My request:", 1)[1].strip()
        return value

    def tool_text(value):
        if isinstance(value, str):
            return value
        if isinstance(value, list):
            return "\n".join(tool_text(item) for item in value)
        if isinstance(value, dict):
            return tool_text(value.get("text", ""))
        return ""

    for number, record in records:
        payload = record.get("payload", {})
        kind = payload.get("type")
        timestamp = record.get("timestamp", "timestamp unavailable")
        if record.get("type") == "response_item" and kind == "custom_tool_call":
            tool_calls[payload.get("call_id")] = payload.get("input", "")
            continue
        if record.get("type") == "response_item" and kind == "custom_tool_call_output" and exchange:
            call = tool_calls.get(payload.get("call_id"), "")
            output = tool_text(payload.get("output", ""))
            direct_web = re.search(r"^\s*(?:text\(await )?tools\.web__run\(", call)
            direct_test = call.strip().startswith("python -m unittest") or (
                "tools.exec_command" in call and "tools.apply_patch" not in call and "-m unittest" in call
            )
            if direct_web:
                link = re.search(r"https?://[^\s)\]]+", output)
                if link:
                    parts.append(f"### Research source - raw line {number} - {timestamp}\n\n{link.group(0).rstrip('.,;')}")
            elif direct_test and "FAILED" not in output:
                result = re.search(r"Ran \d+ tests? in [0-9.]+s", output)
                if result and "OK" in output:
                    parts.append(f"### Verification note - raw line {number} - {timestamp}\n\n{result.group(0)}; OK")
            continue
        label, blocks = None, []
        if record.get("type") == "response_item":
            if kind == "message" and payload.get("role") in ("user", "assistant"):
                label = payload["role"]
                blocks = text_blocks(payload.get("content", []))
            elif kind == "reasoning":
                blocks = [block["text"] for block in payload.get("summary", []) if isinstance(block.get("text"), str)]
                if blocks:
                    label = "Available reasoning summary"
        elif record.get("type") == "event_msg" and not use_messages:
            if kind in ("user_message", "agent_message"):
                label = "user" if kind == "user_message" else "assistant"
                blocks = [payload.get("message", "")]
                if any(payload.get(key) for key in ("images", "local_images", "audio", "local_audio")):
                    blocks.append("[Non-text attachment; see raw export and retain original file]")
        supplied_files = []
        if label == "user":
            for block in blocks:
                if block.lstrip().startswith("# Files mentioned by the user:"):
                    preamble = block.split("## My request:", 1)[0]
                    supplied_files.extend(re.findall(r"(?m)^## ([^:\r\n]+):", preamble))
            cleaned = [readable_prompt(block) for block in blocks]
            blocks = [block for block in cleaned if block and block.strip()]
            if not blocks:
                continue
            exchange += 1
            parts.append(f"## Exchange {exchange}")
            label = "User prompt"
        elif label == "assistant":
            if not exchange:
                continue
            label = "Assistant response"
        if label and blocks:
            count += 1
            parts.extend([f"### {label} - source line {number} - {timestamp}", "\n\n".join(blocks)])
            if supplied_files:
                parts.append(f"### File supplied with prompt - source line {number} - {timestamp}\n\n" + ", ".join(supplied_files))
        if record.get("type") == "compacted":
            parts.append(f"[Compaction marker at source line {number}; no missing history reconstructed]")
    if not count:
        raise ValueError("No supported conversation content found; raw format requires review")
    return str(session_id), "; ".join(models) or "not recorded", "\n\n".join(parts) + "\n"


def rows_at(root):
    path = root / "sessions.csv"
    if not path.exists():
        return []
    with path.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        if reader.fieldnames != FIELDS:
            raise ValueError("Unexpected sessions.csv columns")
        return list(reader)


def preserve(root, source, tool, session_id, model, topic, transcript, data, saved_final=False):
    digest = hashlib.sha256(data).hexdigest()
    rows = rows_at(root)
    previous = [r for r in rows if r["tool"] == tool and r["session_id"] == session_id]
    obsolete = []
    for row in previous:
        for field, directory in (("raw_path", "raw"), ("transcript_path", "transcripts")):
            path = (root / row[field]).resolve()
            if not path.is_relative_to((root / directory / tool).resolve()):
                raise ValueError(f"Evidence path outside expected directory: {path}")
            obsolete.append(path)
        old = (root / row["raw_path"]).read_bytes()
        if hashlib.sha256(old).hexdigest() != row["sha256"]:
            raise ValueError("Existing source hash mismatch; refusing to replace evidence")
        if tool == "codex" and not data.startswith(old):
            raise ValueError("New Codex export does not extend the previous source; refusing to discard history")
    slug = re.sub(r"[^A-Za-z0-9_-]", "_", session_id)[:100]
    name = slug
    raw = Path("raw") / tool / (name + source.suffix)
    readable = Path("transcripts") / tool / (name + ".md")
    for path in (raw, readable):
        (root / path).parent.mkdir(parents=True, exist_ok=True)
    (root / raw).write_bytes(data)
    (root / readable).write_text(transcript, encoding="utf-8")
    rows = [r for r in rows if not (r["tool"] == tool and r["session_id"] == session_id)]
    completeness = "captured through saved final reply; refresh if continued" if saved_final else "snapshot; review required"
    notes = "Source: " + str(source.resolve())
    if tool == "codex":
        records = read_codex(data)
        number, last = records[-1]
        notes += f"; captured through source line {number}, {last.get('timestamp', 'timestamp unavailable')}"
        if not saved_final:
            notes += "; current final reply may not yet be saved; refresh after it is saved"
    rows.append(dict(zip(FIELDS, [datetime.now(timezone.utc).isoformat(), tool, model, session_id, topic, raw.as_posix(), readable.as_posix(), digest, completeness, notes])))
    with (root / "sessions.csv").open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    for path in set(obsolete) - {(root / raw).resolve(), (root / readable).resolve()}:
        path.unlink()
    print(f"Saved {raw} and {readable}")
    return list(set(obsolete + [(root / raw).resolve(), (root / readable).resolve(), (root / 'sessions.csv').resolve()]))


def commit_records(root, paths):
    """Stage only this session's evidence and tracker; never push."""
    repo = root.resolve().parent
    git = ["git", "-C", str(repo), "-c", f"safe.directory={repo.as_posix()}"]
    relative = [path.relative_to(repo).as_posix() for path in paths]
    tracked = subprocess.check_output(git + ["ls-files", "-z", "--", *relative]).decode("utf-8").split("\0")
    relative = [path for path in relative if (repo / path).exists() or path in tracked]
    subprocess.run(git + ["add", "-A", "--", *relative], check=True)
    subprocess.run(git + ["diff", "--cached", "--check", "--", *relative], check=True)
    # --only prevents unrelated pre-staged work from entering this closeout commit.
    subprocess.run(git + ["commit", "--only", "-m", "Refresh saved final conversation record", "--", *relative], check=True)


def wait_for_final(source, timeout):
    """Wait for a new actual assistant final message; never synthesize one."""
    start = len(source.read_bytes().splitlines())
    print("Waiting for the next saved assistant final reply...", flush=True)
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        data = source.read_bytes()
        try:
            records = read_codex(data)
        except ValueError:
            time.sleep(0.1)  # The live writer may be halfway through a JSON line.
            continue
        for number, record in records:
            payload = record.get("payload", {})
            if number > start and record.get("type") == "response_item" and payload.get("type") == "message" and payload.get("role") == "assistant" and (payload.get("phase") == "final" or payload.get("channel") == "final"):
                return data
        time.sleep(0.1)
    raise ValueError("Timed out waiting for a saved final reply; existing records were not changed")


def discover(directory, workspace):
    for path in sorted(directory.rglob("rollout-*.jsonl")):
        try:
            with path.open(encoding="utf-8") as stream:
                meta = json.loads(next(stream)).get("payload", {})
            if os.path.normcase(os.path.abspath(meta.get("cwd", ""))) == os.path.normcase(str(workspace.resolve())):
                print(f"{meta.get('id', 'unknown')}  {path}")
        except (OSError, ValueError, StopIteration):
            print(f"Could not inspect {path}", file=sys.stderr)


def write_pdf(text, path):
    from reportlab.lib import colors
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer

    fonts = Path(os.environ.get("WINDIR", "C:/Windows")) / "Fonts"
    regular, bold, mono = (fonts / name for name in ("segoeui.ttf", "segoeuib.ttf", "consola.ttf"))
    if not all(font.exists() for font in (regular, bold, mono)):
        raise ValueError("PDF requires Segoe UI and Consolas fonts; adapt write_pdf font paths for this OS")
    for name, font in (("RecordBody", regular), ("RecordBold", bold), ("RecordMono", mono)):
        pdfmetrics.registerFont(TTFont(name, str(font)))
    body = ParagraphStyle("Body", fontName="RecordBody", fontSize=9.2, leading=13.5, textColor=colors.HexColor("#263238"), spaceAfter=2, wordWrap="CJK")
    title = ParagraphStyle("Title", parent=body, fontName="RecordBold", fontSize=17, leading=21, textColor=colors.HexColor("#0B4A48"), spaceBefore=12, spaceAfter=9, keepWithNext=True)
    section = ParagraphStyle("Section", parent=body, fontName="RecordBold", fontSize=12, leading=16, textColor=colors.HexColor("#0B4A48"), spaceBefore=12, spaceAfter=5, keepWithNext=True)
    label = ParagraphStyle("Label", parent=body, fontName="RecordBold", fontSize=9.2, leading=13.5, spaceBefore=9, spaceAfter=3, keepWithNext=True)
    bullet = ParagraphStyle("Bullet", parent=body, leftIndent=13, firstLineIndent=-8)
    code = ParagraphStyle("Code", parent=body, fontName="RecordMono", fontSize=8, leading=11, leftIndent=11)
    story = []
    in_code = False
    for line in text.splitlines():
        if line.startswith("```"):
            in_code = not in_code
            story.append(Spacer(1, 4))
            continue
        if not line:
            if not (story and isinstance(story[-1], Paragraph) and getattr(story[-1].style, "keepWithNext", False)):
                story.append(Spacer(1, 5))
            continue
        if in_code:
            story.append(Paragraph(escape(line).replace(" ", "&#160;"), code))
        elif line.startswith("### "):
            story.append(Paragraph(escape(line[4:]), label))
        elif line.startswith("## "):
            story.append(Paragraph(escape(line[3:]), section))
        elif line.startswith("# "):
            story.append(Paragraph(escape(line[2:]), title))
        elif line.startswith(("- ", "* ")):
            story.append(Paragraph(escape(line[2:]), bullet, bulletText="-"))
        else:
            story.append(Paragraph(escape(line), body))

    def page_number(canvas, doc):
        canvas.setFont("RecordBody", 8)
        canvas.setFillColor(colors.HexColor("#60766E"))
        canvas.drawString(42, 25, "IE 535 AI record")
        canvas.drawRightString(570, 25, str(doc.page))

    SimpleDocTemplate(str(path), title="IE 535 AI conversation record", leftMargin=42, rightMargin=42, topMargin=38, bottomMargin=42).build(story, onFirstPage=page_number, onLaterPages=page_number)


def bundle(root, pdf):
    rows = rows_at(root)
    if not rows:
        raise ValueError("No registered exports to compile")
    ordered = sorted(rows, key=lambda r: (r["tool"], r["session_id"], r["captured_utc"]))
    parts = [
        "# IE 535 AI conversation record",
        "Readable saved prompts, corresponding assistant responses and selected source notes. Full original exports and hashes remain in ai_record/raw/ and ai_record/sessions.csv. Capture cutoffs are shown below; missing conversations are not reconstructed.",
        "# Sessions",
    ]
    for index, row in enumerate(ordered, 1):
        label = f"S{index:03d}"
        parts.append(f"{label} | {row['tool']} | {row['topic']} | {row['session_id']} | captured {row['captured_utc']} | {row['completeness']}")
    for index, row in enumerate(ordered, 1):
        raw = root / row["raw_path"]
        data = raw.read_bytes()
        if hashlib.sha256(data).hexdigest() != row["sha256"]:
            raise ValueError(f"Original hash mismatch: {raw}")
        readable = root / row["transcript_path"]
        if row["tool"] == "codex":
            text = codex_transcript(data)[2]
            if not readable.exists() or readable.read_text(encoding="utf-8") != text:
                readable.parent.mkdir(parents=True, exist_ok=True)
                readable.write_text(text, encoding="utf-8")
        else:
            text = readable.read_text(encoding="utf-8")
        parts.extend([f"# S{index:03d} - {row['tool']} - {row['topic']}", text])
    decisions = root / "decisions.md"
    if decisions.exists():
        decision_text = decisions.read_text(encoding="utf-8")
        decision_text = decision_text.split("## Template for future entries", 1)[0].strip()
        parts.extend(["# Decisions and corrections", decision_text])
    output = root / "compiled"
    output.mkdir(parents=True, exist_ok=True)
    text = "\n\n".join(parts)
    (output / "ai_record.md").write_text(text, encoding="utf-8")
    if pdf:
        write_pdf(text, output / "ai_record.pdf")
    print(f"Compiled {len(rows)} sessions into {output}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parent)
    commands = parser.add_subparsers(dest="command", required=True)
    listing = commands.add_parser("list", help="List saved Codex sessions matching this workspace")
    listing.add_argument("--sessions-dir", type=Path, default=Path(os.environ.get("CODEX_HOME", str(Path.home() / ".codex"))) / "sessions")
    listing.add_argument("--workspace", type=Path, default=Path.cwd())
    codex = commands.add_parser("codex", help="Snapshot one explicitly selected saved Codex JSONL")
    codex.add_argument("source", type=Path)
    codex.add_argument("--topic", required=True)
    codex.add_argument("--wait-final", action="store_true", help="Wait for the next newly saved assistant final reply before exporting")
    codex.add_argument("--timeout", type=float, default=180, help="Maximum wait in seconds (default: 180)")
    codex.add_argument("--commit", action="store_true", help="With --wait-final, locally commit only the refreshed session evidence and tracker")
    add = commands.add_parser("add", help="Register a ChatGPT/Claude original plus a verbatim text reading copy")
    add.add_argument("tool", choices=["chatgpt", "claude"])
    add.add_argument("source", type=Path)
    add.add_argument("--transcript", type=Path, help="Required for non-text originals; exact full conversation text, not a summary")
    add.add_argument("--session-id", required=True)
    add.add_argument("--model", default="not recorded")
    add.add_argument("--topic", required=True)
    combined = commands.add_parser("bundle")
    combined.add_argument("--pdf", action="store_true")
    args = parser.parse_args()
    if args.command == "codex" and args.commit and not args.wait_final:
        parser.error("--commit requires --wait-final")
    if args.command == "list":
        discover(args.sessions_dir, args.workspace)
    elif args.command == "bundle":
        bundle(args.root, args.pdf)
    else:
        saved_final = args.command == "codex" and args.wait_final
        data = wait_for_final(args.source, args.timeout) if saved_final else args.source.read_bytes()
        if args.command == "codex":
            session_id, model, text = codex_transcript(data)
            tool = "codex"
        else:
            session_id, model, tool = args.session_id, args.model, args.tool
            if args.transcript:
                text = args.transcript.read_text(encoding="utf-8-sig")
            elif args.source.suffix.lower() in (".txt", ".md"):
                text = data.decode("utf-8-sig")
            else:
                raise ValueError("Supply --transcript with the actual full UTF-8 conversation text; native exports are preserved without guessing their schema")
        paths = preserve(args.root, args.source, tool, session_id, model, args.topic, text, data, saved_final)
        if args.command == "codex" and args.commit:
            commit_records(args.root, paths)


if __name__ == "__main__":
    try:
        main()
    except (ValueError, OSError, ImportError, subprocess.CalledProcessError) as error:
        sys.exit(str(error))
