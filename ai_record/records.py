"""Preserve real AI exports and compile readable, searchable records. No solver code."""
import argparse
import csv
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import sys
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
    parts = [f"# Codex session {session_id}",
             "Snapshot of saved data, not a claim of a complete conversation. Re-export after the final reply.",
             "Verbatim text blocks follow in source order. Labels are generated. System/developer instructions, tool calls/results and encrypted data are omitted here but preserved in raw JSONL. Agent instructions supplied as user messages remain included.",
             "Only available reasoning summaries are included; hidden thinking is unavailable and is never reconstructed. Attachments are not embedded; retain the actual files separately."]
    count = 0
    for number, record in records:
        payload = record.get("payload", {})
        kind = payload.get("type")
        label, blocks = None, []
        if record.get("type") == "response_item":
            if kind == "message" and payload.get("role") in ("user", "assistant"):
                label = payload["role"].title()
                for block in payload.get("content", []):
                    if isinstance(block.get("text"), str):
                        blocks.append(block["text"])
                    else:
                        blocks.append(f"[Non-text content: {block.get('type', 'unknown')}; see raw export and original attachment]")
            elif kind == "reasoning":
                blocks = [block["text"] for block in payload.get("summary", []) if isinstance(block.get("text"), str)]
                if blocks:
                    label = "Available reasoning summary"
        elif record.get("type") == "event_msg" and not use_messages:
            if kind in ("user_message", "agent_message"):
                label = "User" if kind == "user_message" else "Assistant"
                blocks = [payload.get("message", "")]
                if any(payload.get(key) for key in ("images", "local_images", "audio", "local_audio")):
                    blocks.append("[Non-text attachment; see raw export and retain original file]")
        if label:
            count += 1
            parts.extend([f"## {label} - source line {number} - {record.get('timestamp', 'timestamp unavailable')}", "\n\n".join(blocks)])
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


def preserve(root, source, tool, session_id, model, topic, transcript, data):
    digest = hashlib.sha256(data).hexdigest()
    rows = rows_at(root)
    if any(r["tool"] == tool and r["session_id"] == session_id and r["sha256"] == digest for r in rows):
        print("Identical snapshot already registered")
        return
    slug = re.sub(r"[^A-Za-z0-9_-]", "_", session_id)[:100]
    name = f"{slug}-{digest[:16]}"
    raw = Path("raw") / tool / (name + source.suffix)
    readable = Path("transcripts") / tool / (name + ".md")
    for path in (raw, readable):
        (root / path).parent.mkdir(parents=True, exist_ok=True)
    (root / raw).write_bytes(data)
    (root / readable).write_text(transcript, encoding="utf-8")
    rows.append(dict(zip(FIELDS, [datetime.now(timezone.utc).isoformat(), tool, model, session_id, topic, raw.as_posix(), readable.as_posix(), digest, "snapshot; review required", "Source: " + str(source.resolve())])))
    with (root / "sessions.csv").open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    print(f"Saved {raw} and {readable}")


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
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
    font = Path(os.environ.get("WINDIR", "C:/Windows")) / "Fonts" / "consola.ttf"
    if not font.exists():
        raise ValueError("PDF requires a Unicode font; adapt write_pdf font path for this OS")
    pdfmetrics.registerFont(TTFont("Record", str(font)))
    style = ParagraphStyle("Record", fontName="Record", fontSize=8, leading=11, wordWrap="CJK", spaceAfter=2)
    story = []
    for line in text.splitlines():
        # Escape markup and retain indentation; wrap long tokens rather than clip.
        if line:
            story.append(Paragraph(escape(line).replace(" ", "&#160;"), style))
        else:
            story.append(Spacer(1, 5))

    def page_number(canvas, doc):
        canvas.setFont("Record", 8)
        canvas.drawRightString(560, 22, str(doc.page))

    SimpleDocTemplate(str(path), title="IE 535 AI usage record", leftMargin=40, rightMargin=40, topMargin=40, bottomMargin=40).build(story, onFirstPage=page_number, onLaterPages=page_number)


def bundle(root, pdf):
    rows = rows_at(root)
    if not rows:
        raise ValueError("No registered exports to compile")
    parts = ["# IE 535 AI usage record", "Generated from actual registered exports. Snapshots may overlap or be incomplete. Full original exports remain in raw/. No missing conversations reconstructed.", "# Session index", (root / "sessions.csv").read_text(encoding="utf-8")]
    decisions = root / "decisions.md"
    if decisions.exists():
        parts.append(decisions.read_text(encoding="utf-8"))
    for row in sorted(rows, key=lambda r: (r["tool"], r["session_id"], r["captured_utc"])):
        raw = root / row["raw_path"]
        if hashlib.sha256(raw.read_bytes()).hexdigest() != row["sha256"]:
            raise ValueError(f"Original hash mismatch: {raw}")
        text = (root / row["transcript_path"]).read_text(encoding="utf-8")
        if row["tool"] == "codex" and text != codex_transcript(raw.read_bytes())[2]:
            raise ValueError(f"Transcript differs from source: {row['transcript_path']}")
        parts.extend([f"# {row['tool']} / {row['session_id']} / {row['topic']}", f"Captured: {row['captured_utc']} | {row['completeness']} | SHA-256: {row['sha256']}", text])
    output = root / "compiled"
    output.mkdir(parents=True, exist_ok=True)
    text = "\n\n".join(parts)
    (output / "ai_record.md").write_text(text, encoding="utf-8")
    if pdf:
        write_pdf(text, output / "ai_record.pdf")
    print(f"Compiled {len(rows)} snapshots into {output}")


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
    if args.command == "list":
        discover(args.sessions_dir, args.workspace)
    elif args.command == "bundle":
        bundle(args.root, args.pdf)
    else:
        data = args.source.read_bytes()  # One byte snapshot, never modify the live session.
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
        preserve(args.root, args.source, tool, session_id, model, args.topic, text, data)


if __name__ == "__main__":
    try:
        main()
    except (ValueError, OSError, ImportError) as error:
        sys.exit(str(error))
