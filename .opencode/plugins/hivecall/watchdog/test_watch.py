import importlib.util
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

WATCH = Path(__file__).with_name("watch.py")
spec = importlib.util.spec_from_file_location("hivecall_watch", WATCH)
watch = importlib.util.module_from_spec(spec)
spec.loader.exec_module(watch)


class LoadBBTests(unittest.TestCase):
    def test_valid_binding_still_loads_bb_children(self):
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            binding = home / ".bb/plugins/opencode/task-bound.json"
            binding.parent.mkdir(parents=True)
            binding.write_text(json.dumps({"bindings": {"ses_root": "thr_root"}}))
            calls = []

            def parse_json(args, timeout=8.0):
                calls.append(args)
                if args[:2] == ["thread", "list"]:
                    return ([{"id": "thr_child", "parentThreadId": "thr_root"}], "")
                if args[:2] == ["thread", "show"]:
                    return ({"id": "thr_root", "status": "running"}, "")
                return None, "unexpected call"

            expanduser = lambda path: path.replace("~", str(home), 1) if path.startswith("~") else path
            with patch.object(watch.os.path, "expanduser", side_effect=expanduser), \
                 patch.object(watch.BB, "parse_json", side_effect=parse_json), \
                 patch.object(watch.BB, "command", return_value=("[]", "")):
                result = watch.load_bb("thr_root", [], [])

            self.assertTrue(result["binding_valid"])
            self.assertTrue(result["list_valid"])
            self.assertEqual(result["children"], [{"id": "thr_child", "parentThreadId": "thr_root"}])
            self.assertEqual(calls[0], ["thread", "list", "--json"])


class LedgerPathTests(unittest.TestCase):
    def test_ledger_path_built_from_an_empty_repo_is_read_from_the_repo(self):
        # `export REPO=... LEDGER="$REPO/..."` on one line gave LEDGER=/.hivecall/checklist.html and "Proven 0/0".
        with tempfile.TemporaryDirectory() as root:
            ledger = Path(root) / ".hivecall/checklist.html"
            ledger.parent.mkdir()
            ledger.write_text('<li id="ISC-1"><input type="checkbox" checked> a</li>\n<li id="ISC-2"><input type="checkbox"> b</li>')
            for path in ("/.hivecall/checklist.html", ".hivecall/checklist.html"):
                result = watch.parse_isa(path, root)
                self.assertEqual((result["pass"], result["total"]), (1, 2))

class CreditPauseTests(unittest.TestCase):
    def test_credit_stop_once_then_resume(self):
        snapshot = watch.synthetic("none", 100000)
        snapshot["sessions"]["stop_errors"] = [{"id": "ses:1", "session": "ses", "message": "Free usage limit reached"}]
        snapshot["bb"]["children"] = [{"id": "thr_child", "status": "active"}]
        with tempfile.TemporaryDirectory() as root:
            env = {"REPO": root, "ORCH_THREAD": "thr_root", "ORCH_SESSION": "ses", "AUTOMATION_ID": "auto_1"}
            state = {"credit_stops_handled": []}
            with patch.object(watch.BB, "command", return_value=("", "")) as command:
                self.assertEqual(watch.evaluate(snapshot, state, env, False), ["credit-out"])
                self.assertEqual([c.args[0] for c in command.call_args_list], [
                    ["thread", "stop", "thr_root"], ["thread", "stop", "thr_child"],
                    ["automation", "pause", "auto_1"]])
                command.reset_mock()
                watch.evaluate(snapshot, state, env, False)
                self.assertFalse(any(c.args[0][:2] in (["thread", "stop"], ["automation", "pause"])
                                     for c in command.call_args_list))
            self.assertEqual(len((Path(root) / ".lanes/watch-ALERT.txt").read_text().splitlines()), 1)

    def test_each_credit_phrase_pauses(self):
        for message in ("usage limit has been reached", "Free usage limit reached",
                        "out of extra usage", "run out of credits", "monthly usage limit reached",
                        "reached your weekly usage limit", "reached your session usage limit"):
            with self.subTest(message=message), tempfile.TemporaryDirectory() as root:
                snapshot = watch.synthetic("none", 100000)
                snapshot["sessions"]["stop_errors"] = [{"id": "ses:1", "session": "ses", "message": message}]
                with patch.object(watch.BB, "command", return_value=("", "")):
                    self.assertEqual(watch.evaluate(snapshot, {"credit_stops_handled": []}, {"REPO": root, "ORCH_THREAD": "thr_root", "ORCH_SESSION": "ses",
                                                                  "AUTOMATION_ID": "auto_1"}, False),
                                     ["credit-out"])

    def test_rate_limits_do_not_pause(self):
        for message in ("All 1 account(s) are rate-limited. Try again in 10s",
                        "This request would exceed your account's rate limit. Please try again later.",
                        "Error", ""):
            with self.subTest(message=message), tempfile.TemporaryDirectory() as root:
                snapshot = watch.synthetic("none", 100000)
                snapshot["sessions"]["stop_errors"] = [{"id": "ses:1", "session": "ses", "message": message}]
                with patch.object(watch.BB, "command", return_value=("", "")) as command:
                    watch.evaluate(snapshot, {"credit_stops_handled": []}, {"REPO": root, "ORCH_THREAD": "thr_root", "ORCH_SESSION": "ses",
                                                 "AUTOMATION_ID": "auto_1"}, False)
                    self.assertFalse(any(c.args[0][:2] in (["thread", "stop"], ["automation", "pause"])
                                         for c in command.call_args_list))

    def test_baseline_and_ended_child_are_ignored(self):
        snapshot = watch.synthetic("none", 100000)
        snapshot["sessions"]["stop_errors"] = [{"id": "ses:1", "session": "ses", "message": "run out of credits"}]
        with tempfile.TemporaryDirectory() as root, patch.object(watch.BB, "command", return_value=("", "")) as command:
            env = {"REPO": root, "ORCH_THREAD": "thr_root", "ORCH_SESSION": "ses", "AUTOMATION_ID": "auto_1"}
            state = {}
            watch.evaluate(snapshot, state, env, False)
            snapshot["sessions"]["stop_errors"] = [{"id": "ended:2", "session": "ended", "message": "run out of credits"}]
            snapshot["sessions"]["children"] = [{"id": "ended", "time_idle": 1, "idle_outcome": "failed"}]
            watch.evaluate(snapshot, state, env, False)
            self.assertFalse(any(c.args[0][:2] in (["thread", "stop"], ["automation", "pause"])
                                 for c in command.call_args_list))

    def test_failure_retries_without_second_alert(self):
        snapshot = watch.synthetic("none", 100000)
        snapshot["sessions"]["stop_errors"] = [{"id": "ses:1", "session": "ses", "message": "run out of credits"}]
        with tempfile.TemporaryDirectory() as root:
            env = {"REPO": root, "ORCH_THREAD": "thr_root", "ORCH_SESSION": "ses", "AUTOMATION_ID": "auto_1"}
            state = {"credit_stops_handled": []}
            with patch.object(watch.BB, "command", side_effect=[("", "failed"), ("", ""), ("", "")]) as command:
                watch.evaluate(snapshot, state, env, False)
                self.assertEqual(state["credit_stops_handled"], [])
                self.assertEqual(command.call_count, 1)
                watch.evaluate(snapshot, state, env, False)
                self.assertEqual(state["credit_stops_handled"], ["ses:1"])
                self.assertEqual(command.call_count, 3)
            self.assertEqual(len((Path(root) / ".lanes/watch-ALERT.txt").read_text().splitlines()), 1)

    def test_pause_failure_retries_after_threads_stop(self):
        snapshot = watch.synthetic("none", 100000)
        snapshot["sessions"]["stop_errors"] = [{"id": "ses:1", "session": "ses", "message": "run out of credits"}]
        with tempfile.TemporaryDirectory() as root:
            env = {"REPO": root, "ORCH_THREAD": "thr_root", "ORCH_SESSION": "ses", "AUTOMATION_ID": "auto_1"}
            state = {"credit_stops_handled": []}
            with patch.object(watch.BB, "command", side_effect=[("", ""), ("", "failed"), ("", "")]) as command:
                watch.evaluate(snapshot, state, env, False)
                self.assertEqual(state["credit_stops_handled"], [])
                snapshot["bb"]["orch_status"] = "idle"
                snapshot["sessions"]["stop_errors"] = []
                watch.evaluate(snapshot, state, env, False)
                self.assertEqual(state["credit_stops_handled"], ["ses:1"])
                self.assertEqual([c.args[0] for c in command.call_args_list], [
                    ["thread", "stop", "thr_root"], ["automation", "pause", "auto_1"],
                    ["automation", "pause", "auto_1"]])
            self.assertEqual(len((Path(root) / ".lanes/watch-ALERT.txt").read_text().splitlines()), 1)

    def test_copied_layout_and_invalid_patterns(self):
        source = WATCH.parent
        with tempfile.TemporaryDirectory() as root:
            dest = Path(root) / ".hivecall"
            dest.mkdir()
            shutil.copy(source / "watch.py", dest)
            shutil.copytree(source / "hivewatch", dest / "hivewatch")
            config = dest / "credit-out.json"
            shutil.copy(source.parent / "credit-out.json", config)
            script = """
import watch
from unittest.mock import patch
s = watch.synthetic("none", 100000)
s["sessions"]["stop_errors"] = [{"id":"ses:1", "session":"ses", "message":"run out of credits"}]
with patch.object(watch.BB, "command", return_value=("", "")) as cmd:
    result = watch.evaluate(s, {"credit_stops_handled":[]}, {"REPO":".", "ORCH_THREAD":"thr_root", "ORCH_SESSION":"ses", "AUTOMATION_ID":"auto_1"}, False)
    print("MATCHED", "credit-out" in result)
"""
            def run():
                return subprocess.run([sys.executable, "-c", script], cwd=dest, text=True,
                                      capture_output=True, check=True).stdout
            self.assertIn("MATCHED True", run())
            for patterns in ("credits", ["credits", ""], ["credits", 1], ["credits", "  "]):
                config.write_text(json.dumps({"patterns": patterns}))
                self.assertIn("MATCHED False", run())


if __name__ == "__main__":
    unittest.main()
