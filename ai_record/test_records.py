"""Behavior tests for documentation tooling; all fixtures are synthetic, not history."""
import csv
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
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

    def test_invalid_source_fails_without_registering_it(self):
        source = self.root / "broken.jsonl"
        source.write_text('{"type": "session_meta"}\nBROKEN\n', encoding="utf-8")
        result = self.run_cli("codex", source, "--topic", "fixture", success=False)
        self.assertIn("Invalid JSON at source line 2", result.stderr)
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
