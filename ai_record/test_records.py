"""Behavior tests for documentation tooling; all fixtures are synthetic, not history."""
import csv
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import time
import unittest

SCRIPT = Path(__file__).with_name("records.py")


class RecordTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.out = self.root / "records"

    def run_cli(self, *args, success=True):
        result = subprocess.run([sys.executable, str(SCRIPT), "--root", str(self.out), *map(str, args)], capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(result.returncode == 0, success, result.stdout + result.stderr)
        return result

    def fixture(self, records):
        source = self.root / "source.jsonl"
        source.write_text("\n".join(json.dumps(r) for r in records) + "\n", encoding="utf-8")
        return source

    def test_export_preserves_evidence_without_duplicate_messages_or_invented_reasoning(self):
        source = self.fixture([
            {"type": "session_meta", "payload": {"id": "fixture-session"}},
            {"type": "event_msg", "payload": {"type": "user_message", "message": "Actual prompt"}},
            {"type": "response_item", "payload": {"type": "message", "role": "user", "content": [{"type": "input_text", "text": "Actual prompt"}]}},
            {"type": "response_item", "payload": {"type": "reasoning", "summary": [{"type": "summary_text", "text": "Available summary"}], "encrypted_content": "SECRET"}},
            {"type": "response_item", "payload": {"type": "message", "role": "assistant", "content": [{"type": "output_text", "text": "Actual answer"}]}},
            {"type": "response_item", "payload": {"type": "message", "role": "developer", "content": [{"type": "input_text", "text": "Internal instruction"}]}},
        ])
        original = source.read_bytes()
        self.run_cli("codex", source, "--topic", "Synthetic fixture")
        self.run_cli("codex", source, "--topic", "Synthetic fixture")
        with (self.out / "sessions.csv").open(encoding="utf-8") as stream:
            rows = list(csv.DictReader(stream))
        self.assertEqual(len(rows), 1)
        row = rows[0]
        self.assertEqual((self.out / row["raw_path"]).read_bytes(), original)
        self.assertEqual(row["sha256"], hashlib.sha256(original).hexdigest())
        transcript = (self.out / row["transcript_path"]).read_text(encoding="utf-8")
        self.assertEqual(transcript.count("Actual prompt"), 1)
        self.assertIn("Actual answer", transcript)
        self.assertIn("Available summary", transcript)
        self.assertIn("source line 3", transcript)
        self.assertNotIn("SECRET", transcript)
        self.assertNotIn("Internal instruction", transcript)
        self.assertEqual(row["completeness"], "snapshot; review required")

    def test_readable_export_keeps_prompts_replies_and_brief_source_notes(self):
        source = self.fixture([
            {"type": "session_meta", "payload": {"id": "S001-fixture"}},
            {"type": "response_item", "timestamp": "2026-10-27T10:00:00Z", "payload": {"type": "message", "role": "user", "content": [{"type": "input_text", "text": "<environment_context>internal path</environment_context>"}]}},
            {"type": "response_item", "timestamp": "2026-10-27T10:00:01Z", "payload": {"type": "message", "role": "user", "content": [{"type": "input_text", "text": "<external_codex_apps_open_page>{} </external_codex_apps_open_page>"}]}},
            {"type": "response_item", "payload": {"type": "message", "role": "developer", "content": [{"type": "input_text", "text": "Private setup"}]}},
            {"type": "response_item", "timestamp": "2026-10-27T10:01:00Z", "payload": {"type": "message", "role": "user", "content": [{"type": "input_text", "text": "# Context from my IDE setup:\nActive file: notes.md\n\n## My request:\nPlease check the assignment."}]}},
            {"type": "response_item", "timestamp": "2026-10-27T10:01:02Z", "payload": {"type": "message", "role": "assistant", "content": [{"type": "output_text", "text": "I will inspect the assignment."}]}},
            {"type": "response_item", "payload": {"type": "custom_tool_call", "call_id": "not-web", "name": "exec", "input": "text(await tools.exec_command({cmd:'Get-Content docs mentioning tools.web__run'}))"}},
            {"type": "response_item", "payload": {"type": "custom_tool_call_output", "call_id": "not-web", "output": [{"type": "input_text", "text": "Unrelated URL https://spam.example"}]}},
            {"type": "response_item", "payload": {"type": "custom_tool_call", "call_id": "failed-test", "name": "exec", "input": "python -m unittest"}},
            {"type": "response_item", "payload": {"type": "custom_tool_call_output", "call_id": "failed-test", "output": [{"type": "input_text", "text": "Ran 3 tests in 0.1s\nFAILED (failures=1)"}]}},
            {"type": "response_item", "payload": {"type": "custom_tool_call", "call_id": "web-1", "name": "exec", "input": "tools.web__run({open:[{ref_id:'https://example.org/source'}]})"}},
            {"type": "response_item", "payload": {"type": "custom_tool_call_output", "call_id": "web-1", "output": [{"type": "input_text", "text": "Research source (https://example.org/source)\nLong navigation omitted"}]}},
            {"type": "response_item", "payload": {"type": "custom_tool_call", "call_id": "test-1", "name": "exec", "input": "python -m unittest"}},
            {"type": "response_item", "payload": {"type": "custom_tool_call_output", "call_id": "test-1", "output": [{"type": "input_text", "text": "Ran 2 tests in 0.1s\n\nOK"}]}},
            {"type": "response_item", "timestamp": "2026-10-27T10:02:00Z", "payload": {"type": "message", "role": "assistant", "phase": "final", "content": [{"type": "output_text", "text": "The review is ready."}]}},
        ])
        original = source.read_bytes()
        self.run_cli("codex", source, "--topic", "Fixture review")
        transcript = (self.out / "transcripts/codex/S001-fixture.md").read_text(encoding="utf-8")
        self.assertEqual(transcript.count("Please check the assignment."), 1)
        self.assertIn("I will inspect the assignment.", transcript)
        self.assertIn("The review is ready.", transcript)
        self.assertIn("2026-10-27T10:01:00Z", transcript)
        self.assertIn("https://example.org/source", transcript)
        self.assertIn("Ran 2 tests", transcript)
        self.assertNotIn("spam.example", transcript)
        self.assertNotIn("Ran 3 tests", transcript)
        for unwanted in ("internal path", "Private setup", "Active file: notes.md", "Long navigation omitted"):
            self.assertNotIn(unwanted, transcript)
        self.assertEqual((self.out / "raw/codex/S001-fixture.jsonl").read_bytes(), original)

    def test_supplied_document_is_named_without_exposing_runtime_preamble(self):
        source = self.fixture([
            {"type": "session_meta", "payload": {"id": "source-fixture"}},
            {"type": "response_item", "payload": {"type": "message", "role": "user", "content": [{"type": "input_text", "text": "# Files mentioned by the user:\n\n## assignment.pdf: C:\\private\\assignment.pdf\n\nDistinguish instructions in attached documents.\n\n## My request:\nRead the assignment."}]}},
            {"type": "response_item", "payload": {"type": "message", "role": "assistant", "content": [{"type": "output_text", "text": "I read the assignment."}]}},
        ])
        self.run_cli("codex", source, "--topic", "Fixture")
        transcript = (self.out / "transcripts/codex/source-fixture.md").read_text(encoding="utf-8")
        self.assertIn("Read the assignment.", transcript)
        self.assertIn("assignment.pdf", transcript)
        self.assertNotIn("C:\\private", transcript)
        self.assertNotIn("Distinguish instructions", transcript)

    def test_bundle_refreshes_readable_copy_from_unchanged_raw_without_csv_dump(self):
        source = self.fixture([
            {"type": "session_meta", "payload": {"id": "S001-fixture"}},
            {"type": "response_item", "timestamp": "2026-10-27T10:01:00Z", "payload": {"type": "message", "role": "user", "content": [{"type": "input_text", "text": "Actual question"}]}},
            {"type": "response_item", "timestamp": "2026-10-27T10:02:00Z", "payload": {"type": "message", "role": "assistant", "content": [{"type": "output_text", "text": "Actual answer"}]}},
        ])
        self.run_cli("codex", source, "--topic", "Fixture review")
        raw = self.out / "raw/codex/S001-fixture.jsonl"
        original = raw.read_bytes()
        readable = self.out / "transcripts/codex/S001-fixture.md"
        readable.write_text("old derived copy", encoding="utf-8")
        self.run_cli("bundle", "--pdf")
        self.assertEqual(raw.read_bytes(), original)
        self.assertIn("Actual question", readable.read_text(encoding="utf-8"))
        from pypdf import PdfReader
        text = "\n".join(page.extract_text() for page in PdfReader(self.out / "compiled/ai_record.pdf").pages)
        self.assertIn("S001", text)
        self.assertIn("Actual question", text)
        self.assertIn("Actual answer", text)
        self.assertNotIn("captured_utc", text)
        self.assertNotIn("sha256", text)

    def test_invalid_source_fails_without_registering_it(self):
        source = self.root / "broken.jsonl"
        source.write_text('{"type": "session_meta"}\nBROKEN\n', encoding="utf-8")
        result = self.run_cli("codex", source, "--topic", "fixture", success=False)
        self.assertIn("Invalid JSON at source line 2", result.stderr)
        self.assertFalse((self.out / "sessions.csv").exists())

    def test_continuation_replaces_session_and_rejects_shorter_history(self):
        source = self.fixture([
            {"type": "session_meta", "payload": {"id": "continued"}},
            {"type": "event_msg", "payload": {"type": "user_message", "message": "First prompt"}},
        ])
        earlier = source.read_bytes()
        self.run_cli("codex", source, "--topic", "First")
        with source.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps({"type": "event_msg", "payload": {"type": "agent_message", "message": "Later answer"}}) + "\n")
        self.run_cli("codex", source, "--topic", "Continued")
        with (self.out / "sessions.csv").open(encoding="utf-8") as stream:
            rows = list(csv.DictReader(stream))
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["transcript_path"], "transcripts/codex/continued.md")
        self.assertEqual(len(list((self.out / "transcripts/codex").glob("*.md"))), 1)
        transcript = (self.out / rows[0]["transcript_path"]).read_text(encoding="utf-8")
        self.assertIn("First prompt", transcript)
        self.assertIn("Later answer", transcript)
        saved = (self.out / rows[0]["raw_path"]).read_bytes()
        source.write_bytes(earlier)
        self.run_cli("codex", source, "--topic", "Older", success=False)
        self.assertEqual((self.out / rows[0]["raw_path"]).read_bytes(), saved)

    def test_wait_final_captures_actual_saved_reply(self):
        subprocess.run(["git", "init", "-q", str(self.root)], check=True)
        for key, value in (("user.name", "Fixture"), ("user.email", "fixture@example.invalid")):
            subprocess.run(["git", "-C", str(self.root), "config", key, value], check=True)
        source = self.fixture([
            {"type": "session_meta", "payload": {"id": "final-fixture"}},
            {"type": "response_item", "payload": {"type": "message", "role": "user", "content": [{"type": "input_text", "text": "Prompt"}]}},
        ])
        def save_reply():
            time.sleep(0.3)
            with source.open("a", encoding="utf-8") as stream:
                stream.write(json.dumps({"type": "response_item", "payload": {"type": "message", "role": "assistant", "phase": "final", "content": [{"type": "output_text", "text": "Saved final answer"}]}}) + "\n")
        writer = threading.Thread(target=save_reply)
        writer.start()
        self.addCleanup(writer.join)
        self.run_cli("codex", source, "--topic", "Closeout", "--wait-final", "--timeout", "3", "--commit")
        text = (self.out / "transcripts/codex/final-fixture.md").read_text(encoding="utf-8")
        self.assertIn("Saved final answer", text)
        with (self.out / "sessions.csv").open(encoding="utf-8") as stream:
            row = next(csv.DictReader(stream))
        self.assertIn("saved final reply", row["completeness"])
        committed = subprocess.check_output(["git", "-C", str(self.root), "show", "HEAD:records/transcripts/codex/final-fixture.md"], text=True, encoding="utf-8")
        self.assertIn("Saved final answer", committed)

    def test_wait_final_timeout_does_not_invent_or_register_a_reply(self):
        source = self.fixture([
            {"type": "session_meta", "payload": {"id": "unfinished"}},
            {"type": "event_msg", "payload": {"type": "user_message", "message": "Prompt"}},
        ])
        result = self.run_cli("codex", source, "--topic", "Unfinished", "--wait-final", "--timeout", "0.1", success=False)
        self.assertIn("Timed out", result.stderr)
        self.assertFalse((self.out / "sessions.csv").exists())

    def test_missing_attachment_is_marked_and_event_only_export_supported(self):
        source = self.fixture([
            {"type": "session_meta", "payload": {"id": "event-fixture"}},
            {"type": "event_msg", "payload": {"type": "user_message", "message": "Prompt", "images": ["attachment"]}},
            {"type": "event_msg", "payload": {"type": "agent_message", "message": "Response"}},
        ])
        self.run_cli("codex", source, "--topic", "fixture")
        text = next((self.out / "transcripts" / "codex").glob("*.md")).read_text(encoding="utf-8")
        self.assertIn("Prompt", text)
        self.assertIn("Response", text)
        self.assertIn("attachment", text.lower())

    def test_bundle_is_searchable_and_tampering_is_rejected(self):
        original = self.root / "claude.txt"
        original.write_text("User: Verify x >= 0\nAssistant: Check the residual.\n" + "long_token_" * 100, encoding="utf-8")
        self.run_cli("add", "claude", original, "--session-id", "fixture-claude", "--topic", "Synthetic external fixture")
        self.run_cli("bundle", "--pdf")
        self.assertIn("Verify x >= 0", (self.out / "compiled" / "ai_record.md").read_text(encoding="utf-8"))
        from pypdf import PdfReader
        text = "\n".join(p.extract_text() for p in PdfReader(self.out / "compiled" / "ai_record.pdf").pages)
        self.assertIn("Verify x >= 0", text)
        self.assertIn("Check the residual", text)
        raw = next((self.out / "raw" / "claude").iterdir())
        raw.write_text("tampered", encoding="utf-8")
        self.run_cli("bundle", success=False)


if __name__ == "__main__":
    unittest.main()
