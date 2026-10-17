import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from pathlib import Path
from unittest.mock import patch


RUNNER = Path(__file__).with_name("run-gate.py")
SPEC = importlib.util.spec_from_file_location("hivecall_run_gate", RUNNER)
run_gate = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(run_gate)


class ParseJudgmentTests(unittest.TestCase):
    def test_rejects_malformed_response(self):
        with self.assertRaises(ValueError):
            run_gate.parse_judgment('{"verdict": "PASS"')

    def test_rejects_trailing_pass_after_fail(self):
        with self.assertRaises(ValueError):
            run_gate.parse_judgment('{"verdict":"REJECT"} PASS')

    def test_rejects_two_objects(self):
        with self.assertRaises(ValueError):
            run_gate.parse_judgment('{"verdict":"REJECT"} {"verdict":"PASS"}')

    def test_rejects_conflicting_prefix_before_pass(self):
        with self.assertRaises(ValueError):
            run_gate.parse_judgment('verdict: REJECT\n{"verdict":"PASS"}')

    def test_rejects_unknown_verdict(self):
        with self.assertRaises(ValueError):
            run_gate.parse_judgment('{"verdict":"UNKNOWN"}')

    def test_rejects_non_string_verdict(self):
        with self.assertRaises(ValueError):
            run_gate.parse_judgment('{"verdict":[]}')


class PreviewRedactionTests(unittest.TestCase):
    def test_preview_redacts_full_payload_without_calling_judge(self):
        proposal = {
            "target_behaviors": ["one behavior"],
            "owning_file": ".agents/skills/hivecall/SKILL.md",
            "proposed_edit": "Use path /Users/fixture-person/private and host 192.168.77.42",
            "verification": "check one observable result",
            "trace_evidence": {
                "source": "fixture",
                "thread_id": "fixture-thread",
                "moment": "test moment",
                "observations": "saw the relevant behavior",
            },
            "cause_class": "one_off",
            "credentials": {
                "api_key": "sk-fixtureSecret123456",
                "password": "quoted-json-credential-fixture",
            },
        }
        with tempfile.TemporaryDirectory() as directory:
            proposal_path = Path(directory) / "proposal.json"
            proposal_path.write_text(json.dumps(proposal), encoding="utf-8")
            called_path = Path(directory) / "judge-was-called"
            fake_opencode = Path(directory) / "opencode"
            fake_opencode.write_text('#!/bin/sh\n: > "$GATE_TEST_MARKER"\nexit 86\n', encoding="utf-8")
            fake_opencode.chmod(0o755)
            environment = os.environ.copy()
            environment["PATH"] = directory + os.pathsep + environment.get("PATH", "")
            environment["GATE_TEST_MARKER"] = str(called_path)
            result = subprocess.run(
                [sys.executable, str(RUNNER), "--proposal", str(proposal_path), "--preview"],
                text=True,
                capture_output=True,
                env=environment,
                check=False,
            )
            self.assertFalse(called_path.exists(), "--preview invoked the judge")

        self.assertEqual(result.returncode, 0, result.stderr)
        for planted in (
            "/Users/fixture-person/private",
            "192.168.77.42",
            "sk-fixtureSecret123456",
            "quoted-json-credential-fixture",
        ):
            self.assertNotIn(planted, result.stdout)
        self.assertIn("[path]", result.stdout)
        self.assertIn("[private-url]", result.stdout)
        self.assertIn("[secret]", result.stdout)
        self.assertIn("<proposal-json>", result.stdout)
        self.assertIn("Return exactly one compact JSONL line per input row", result.stdout)
        self.assertIn("every hard gate passes and the score is at least 80", result.stdout)


class RetryTests(unittest.TestCase):
    def run_gate(self, directory):
        proposal = Path(__file__).with_name("fixtures") / "no-observed-failure.json"
        output = Path(directory) / "gate-test.json"
        cache = Path(directory) / "cache"
        batch = Path(directory) / "pending.jsonl"
        stdout = StringIO()
        stderr = StringIO()
        argv = [str(RUNNER), "--proposal", str(proposal), "--output", str(output),
                "--cache-dir", str(cache), "--export-prompts", str(batch)]
        with patch.object(sys, "argv", argv):
            with redirect_stdout(stdout), redirect_stderr(stderr):
                status = run_gate.main()
        return status, output, cache, batch, stdout.getvalue(), stderr.getvalue()

    def import_answer(self, cache, batch, directory, answer):
        answer_file = Path(directory) / "answers.jsonl"
        request = json.loads(batch.read_text(encoding="utf-8").splitlines()[0])
        answer_file.write_text(json.dumps({"id": request["id"], "answer": answer}) + "\n",
                               encoding="utf-8")
        with patch.object(sys, "argv", [str(RUNNER), "import", "--answers", str(answer_file),
                                         "--cache-dir", str(cache)]), redirect_stdout(StringIO()):
            self.assertEqual(run_gate.main(), 0)

    def test_malformed_output_retries_once_and_saves_redacted_replies(self):
        valid_reject = json.dumps({
            "verdict": "REJECT",
            "score": None,
            "reasons": ["unsupported evidence"],
            "hard_gate_failures": ["no observed failure"],
            "rubric_scores": {},
        })
        with tempfile.TemporaryDirectory() as directory:
            status, output, cache, batch, stdout, _ = self.run_gate(directory)
            self.assertEqual(status, 0)
            self.assertIn("awaiting answers:", stdout)
            self.import_answer(cache, batch, directory, '{"api_key":"sk-fixtureSecret123456"')
            status, output, cache, batch, _, _ = self.run_gate(directory)
            self.assertEqual(status, 0)
            self.import_answer(cache, batch, directory, valid_reject)
            status, output, _, _, _, _ = self.run_gate(directory)
            first_reply = output.with_name("gate-test-reply-1.json")
            second_reply = output.with_name("gate-test-reply-2.json")
            self.assertEqual(status, 0)
            self.assertEqual(json.loads(output.read_text())["verdict"], "REJECT")
            self.assertNotIn("sk-fixtureSecret123456", first_reply.read_text())
            self.assertTrue(second_reply.exists())

    def test_two_malformed_replies_write_error_not_pass(self):
        with tempfile.TemporaryDirectory() as directory:
            status, output, cache, batch, _, _ = self.run_gate(directory)
            self.assertEqual(status, 0)
            self.import_answer(cache, batch, directory, "not-json")
            status, output, cache, batch, _, _ = self.run_gate(directory)
            self.assertEqual(status, 0)
            self.import_answer(cache, batch, directory, '{"verdict":"PASS"')
            status, output, _, _, _, _ = self.run_gate(directory)
            result = json.loads(output.read_text())
            self.assertEqual(status, 2)
            self.assertEqual(result["verdict"], "ERROR")
            self.assertNotEqual(result["verdict"], "PASS")
            self.assertTrue(output.with_name("gate-test-reply-1.json").exists())
            self.assertTrue(output.with_name("gate-test-reply-2.json").exists())


if __name__ == "__main__":
    unittest.main()
