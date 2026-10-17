#!/usr/bin/env python3
"""Offline regressions for replay checkpoints, rate limits, and call budgets."""

import argparse
from contextlib import redirect_stderr, redirect_stdout
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from io import StringIO
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import time
import urllib.error
import unittest
from urllib.request import Request
from unittest.mock import patch


HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "gate"))
import run as replay  # noqa: E402
import judge  # noqa: E402


class RetryServer(BaseHTTPRequestHandler):
    calls = 0

    def do_GET(self):
        type(self).calls += 1
        if type(self).calls == 1:
            self.send_response(429)
            self.send_header("Retry-After", "1")
            self.end_headers()
            return
        body = b'{"ok":true}'
        self.send_response(200)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *_args):
        pass


class ReplayCheckpointTests(unittest.TestCase):
    def test_run_identity_keeps_replicates_independent_and_resumable(self):
        with tempfile.TemporaryDirectory() as directory:
            runtime = replay.CallRuntime(directory)
            calls = []

            def sample():
                calls.append(len(calls) + 1)
                return f"sample-{calls[-1]}"

            payload = {"context": "redacted"}
            current = runtime.call("tested-model", "fixture", payload, sample,
                                   identity="report=identity|role=current|moment=m1")
            replicate = runtime.call("tested-model", "fixture", payload, sample,
                                      identity="report=identity|role=replicate-1|moment=m1")
            resumed = runtime.call("tested-model", "fixture", payload,
                                    lambda: self.fail("resume missed the current checkpoint"),
                                    identity="report=identity|role=current|moment=m1")
            other_report = runtime.call("tested-model", "fixture", payload, sample,
                                        identity="report=other|role=current|moment=m1")
            self.assertEqual((current, replicate, resumed, other_report),
                             ("sample-1", "sample-2", "sample-1", "sample-3"))
            self.assertEqual(len(calls), 3)
            self.assertEqual(len(list(Path(directory).glob("[0-9a-f]" * 64 + ".json"))), 3)

    def test_unknown_answers_never_pass_and_are_excluded_from_scores(self):
        moment = {"behavior": 2, "fixedCheck": {"label": "proof_not_detected"}}
        self.assertIsNone(replay.candidate_rule_label(moment, 2, ""))
        self.assertIsNone(replay.candidate_rule_label(moment, 2, "Continue without claiming completion"))
        self.assertEqual(replay.candidate_rule_label(moment, 2, "I ticked the item complete"), "FAIL")
        labels = replay.final_pair_labels(None, None, None, None, None, None, None)
        self.assertEqual(labels, {"current": "UNKNOWN", "changed": "UNKNOWN"})
        self.assertEqual(replay.score_labels(["PASS", "UNKNOWN", "FAIL"]), 50)
        self.assertEqual(replay.unknown_count(["PASS", "UNKNOWN", "FAIL"]), 1)
        self.assertEqual(replay.paired_bootstrap(["PASS", "UNKNOWN"], ["FAIL", "PASS"], 1)["n"], 1)
        scorecard, rows, *_ = replay.score_baseline([{
            "behavior": 1, "runId": "empty", "momentId": "m1", "actualNextAction": {"text": ""},
            "fixedCheck": {"label": "tick"},
        }], 1)
        self.assertEqual(rows[0]["final"], "UNKNOWN")
        self.assertEqual((scorecard["1"]["score"], scorecard["1"]["unknown"]), (None, 1))
        totals = {behavior: int(behavior == 1) for behavior in range(1, 8)}
        for behavior, entry in scorecard.items():
            entry["totalMoments"] = totals[int(behavior)]
            entry["rawMoments"] = totals[int(behavior)]
        report = replay.render_baseline(scorecard, totals, totals,
                                        argparse.Namespace(per_behavior=1, seed=1), {}, [], {}, {})
        self.assertIn("0 / 1 / 1 / 1", report)

    def test_score_baseline_uses_disjoint_fixed_seed_calibration_partition(self):
        moments = [{"behavior": 1, "runId": "fixture", "momentId": f"m{i}",
                    "context": f"context-{i}", "actualNextAction": {"text": f"action-{i}"},
                    "fixedCheck": {"label": "tick"}} for i in range(12)]
        with patch.object(replay, "clef_label", return_value=("PASS", 0.95)), \
                patch.object(replay, "cloud_judge", return_value='{"label":"PASS"}'):
            scorecard, rows, _, _, examples = replay.score_baseline(moments, 17)
            repeated_examples = replay.score_baseline(moments, 17)[4]
        contexts = {moment["momentId"]: moment["context"] for moment in moments}
        scored_contexts = {contexts[row["momentId"]] for row in rows if row["behavior"] == 1}
        example_contexts = {example["context"] for example in examples[1]}
        self.assertEqual(scorecard["1"]["calibrationMoments"], 2)
        self.assertEqual(scorecard["1"]["moments"], 10)
        self.assertEqual(examples[1], repeated_examples[1])
        self.assertTrue(example_contexts.isdisjoint(scored_contexts))

    def test_offline_rule_only_precheck_does_not_append_result_row(self):
        old_urlopen = replay.urllib.request.urlopen
        old_judge = replay.judge_client.judge
        try:
            import offline
            replay.urllib.request.urlopen = old_urlopen
            replay.judge_client.judge = old_judge
            with tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                dataset = root / "dataset.jsonl"
                dataset.write_text("", encoding="utf-8")
                result_rows = root / "results.jsonl"
                old_here, old_results = offline.HERE, replay.RESULTS
                try:
                    offline.HERE = root / "replay"
                    replay.RESULTS = result_rows
                    args = argparse.Namespace(archive_only=True, exclude_run_id=[],
                                              dataset=str(dataset), per_behavior=30,
                                              seed=4, skill="unused")
                    with redirect_stdout(StringIO()):
                        offline.run(args)
                    self.assertFalse(result_rows.exists())
                finally:
                    offline.HERE, replay.RESULTS = old_here, old_results
        finally:
            replay.urllib.request.urlopen = old_urlopen
            replay.judge_client.judge = old_judge

    def test_few_shots_use_only_build_partition_and_exclude_evaluated_moment(self):
        def labeled(moment_id, week):
            return {"runId": "run", "momentId": moment_id, "week": week, "behavior": 1,
                    "context": moment_id, "actualNextAction": {"text": "tick item"},
                    "fixedCheck": {"label": "tick"}}

        heldout, evaluated, build, later = (labeled("heldout", "2026-W41"),
                                             labeled("evaluated", "2026-W42"),
                                             labeled("build", "2026-W42"),
                                             labeled("later", "2026-W43"))
        examples = replay.examples_for([heldout, evaluated, build, later], 1,
                                       build_week="2026-W42", excluded=[evaluated])
        self.assertEqual([example["context"] for example in examples], ["build", "later"])
        self.assertEqual(replay.examples_for([heldout], 1, build_week="2026-W42"), [])
        args = argparse.Namespace(report_tag="offline", model="fixture", judge_model="fixture",
                                  build_week="2026-W42", per_behavior=1, seed=1)
        scores = {str(b): {"current": None, "changed": None} for b in range(1, 8)}
        trust = {str(b): "not-measured" for b in range(1, 8)}
        week_rows = {"2026-W41": {"2": {"current": ["UNKNOWN"], "changed": ["UNKNOWN"]}}}
        report = replay.render_eval(args, {}, 0, scores, trust, {}, None, False, True,
                                    week_rows, [], [],
                                    "REJECT", [], "moments.json", {"zeroWorker": 0,
                                    "liveWorkerControl": 0}, False, {}, [2])
        self.assertIn("none available for behaviors: 2", report)
        self.assertIn("1/1", report)

    def test_fail_probability_is_confident_and_does_not_trigger_adjudication(self):
        label, confidence = replay.clef_probability_label(0.01)
        self.assertEqual((label, confidence), ("FAIL", 0.99))
        self.assertFalse(replay.needs_judge(None, label, confidence, False))
        self.assertEqual(replay.clef_probability_label(float("nan")), (None, None))

    def test_retry_after_above_cap_returns_rate_limited_without_sleep(self):
        error = urllib.error.HTTPError(
            "http://offline.test", 429, "rate limited", {"Retry-After": "601"}, None)
        with patch.object(judge.urllib.request, "urlopen", side_effect=error), \
                patch.object(judge.time, "sleep") as sleep, redirect_stderr(StringIO()):
            with self.assertRaises(judge.RateLimitError) as stopped:
                judge.request_with_retry(Request("http://offline.test"), timeout=1)
        self.assertEqual((stopped.exception.status, stopped.exception.attempts), (429, 1))
        sleep.assert_not_called()
        with tempfile.TemporaryDirectory() as directory:
            old_runtime = replay.RUNTIME
            try:
                replay.RUNTIME = replay.CallRuntime(directory)
                replay.RUNTIME.set_estimates({"judge": 1})
                self.assertIn("BLOCKED: rate limited", replay.blocked_message("rate limited"))
            finally:
                replay.RUNTIME = old_runtime

    def test_429_honors_retry_after_and_checkpoints_answer(self):
        RetryServer.calls = 0
        server = ThreadingHTTPServer(("127.0.0.1", 0), RetryServer)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            with tempfile.TemporaryDirectory() as directory, redirect_stderr(StringIO()):
                runtime = replay.CallRuntime(directory)
                runtime.set_estimates({"judge": 1})
                request = Request(f"http://127.0.0.1:{server.server_port}/")
                started = time.monotonic()

                def invoke():
                    with judge.request_with_retry(request, timeout=3) as response:
                        return json.load(response)

                result = runtime.call("judge", "fixture-model", {"user": "redacted"}, invoke)
                elapsed = time.monotonic() - started
                self.assertEqual(result, {"ok": True})
                self.assertGreaterEqual(elapsed, 0.8)
                self.assertEqual(RetryServer.calls, 2)
                self.assertEqual(len(list(Path(directory).glob("[0-9a-f]" * 64 + ".json"))), 1)

                resumed = replay.CallRuntime(directory)
                self.assertEqual(resumed.call(
                    "judge", "fixture-model", {"user": "redacted"},
                    lambda: self.fail("cached HTTP answer was requested again")), result)
                self.assertEqual(RetryServer.calls, 2)
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)

    def test_reopened_cache_skips_completed_items(self):
        with tempfile.TemporaryDirectory() as directory:
            environment = os.environ.copy()
            environment["PYTHONPATH"] = os.pathsep.join(
                (str(HERE), str(HERE.parent / "gate"), environment.get("PYTHONPATH", "")))
            first = (
                "import os, sys; from run import CallRuntime; "
                "r=CallRuntime(sys.argv[1]); r.set_estimates({'Clef': 2}); "
                "r.call('Clef', 'clef', {'q':'one'}, lambda:'PASS'); os._exit(23)"
            )
            killed = subprocess.run([sys.executable, "-c", first, directory],
                                    env=environment, capture_output=True, text=True)
            self.assertEqual(killed.returncode, 23, killed.stderr)
            resumed = (
                "import sys; from run import CallRuntime; "
                "r=CallRuntime(sys.argv[1]); r.set_estimates({'Clef': 2}); "
                "a=r.call('Clef','clef',{'q':'one'},lambda:sys.exit('first item repeated')); "
                "b=r.call('Clef','clef',{'q':'two'},lambda:'FAIL'); print(a+'|'+b)"
            )
            result = subprocess.run([sys.executable, "-c", resumed, directory],
                                    env=environment, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout.strip(), "PASS|FAIL")

    def test_max_calls_blocks_baseline_without_result_row(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            dataset = root / "dataset.jsonl"
            rows = []
            for behavior, fixed in ((1, {"label": "tick"}),
                                    (2, {"label": "proof_present"}),
                                    (3, {"label": "open", "gapMinutes": 45})):
                for index in range(10):
                    rows.append({"recordType": "run", "runId": f"r{behavior}-{index}",
                                 "week": "2026-W42", "moments": [{
                                     "behavior": behavior, "momentId": f"m{behavior}-{index}",
                                     "context": "redacted fixture context",
                                     "actualNextAction": {"text": "fixture action"},
                                     "fixedCheck": fixed,
                                 }]})
            dataset.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")
            skill = root / "SKILL.md"
            skill.write_text("fixture skill", encoding="utf-8")
            result_rows = root / "results.jsonl"
            old_here, old_results, old_runtime = replay.HERE, replay.RESULTS, replay.RUNTIME
            old_opt_in = os.environ.get("HIVECALL_ALLOW_DATASET_CLOUD")
            try:
                replay.HERE = root / "replay"
                replay.RESULTS = result_rows
                replay.RUNTIME = replay.CallRuntime(root / "cache", max_calls=0)
                os.environ["HIVECALL_ALLOW_DATASET_CLOUD"] = "1"
                args = argparse.Namespace(dataset=str(dataset), exclude_run_id=[], per_behavior=10,
                                          seed=4, skill=str(skill))
                with redirect_stderr(StringIO()), self.assertRaises(SystemExit) as stopped:
                    replay.run_baseline(args)
                self.assertIn("BLOCKED: max-calls reached", str(stopped.exception))
                self.assertIn("0 calls cached", str(stopped.exception))
                self.assertFalse(result_rows.exists())
                self.assertIn("**Status: BLOCKED**", (replay.HERE / "reports/baseline.md").read_text())
            finally:
                replay.HERE, replay.RESULTS, replay.RUNTIME = old_here, old_results, old_runtime
                if old_opt_in is None:
                    os.environ.pop("HIVECALL_ALLOW_DATASET_CLOUD", None)
                else:
                    os.environ["HIVECALL_ALLOW_DATASET_CLOUD"] = old_opt_in

    def test_incomplete_baseline_does_not_append_result_row(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            dataset = root / "dataset.jsonl"
            rows = [{"recordType": "run", "runId": f"r{index}", "moments": [{
                "behavior": 1, "momentId": f"m{index}", "actualNextAction": {"text": "tick"},
                "fixedCheck": {"label": "tick"}}]} for index in range(9)]
            dataset.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")
            skill = root / "SKILL.md"
            skill.write_text("fixture skill", encoding="utf-8")
            result_rows = root / "results.jsonl"
            old_here, old_results, old_runtime = replay.HERE, replay.RESULTS, replay.RUNTIME
            try:
                replay.HERE = root / "replay"
                replay.RESULTS = result_rows
                replay.RUNTIME = replay.CallRuntime(root / "cache")
                args = argparse.Namespace(dataset=str(dataset), exclude_run_id=[], per_behavior=30,
                                          seed=4, skill=str(skill))
                with redirect_stderr(StringIO()), redirect_stdout(StringIO()), \
                        self.assertRaises(SystemExit) as stopped:
                    replay.run_baseline(args)
                self.assertIn("behavior 1 has only 9", str(stopped.exception))
                self.assertFalse(result_rows.exists())
                self.assertIn("baseline incomplete", (replay.HERE / "reports/baseline.md").read_text())
            finally:
                replay.HERE, replay.RESULTS, replay.RUNTIME = old_here, old_results, old_runtime


if __name__ == "__main__":
    unittest.main()
