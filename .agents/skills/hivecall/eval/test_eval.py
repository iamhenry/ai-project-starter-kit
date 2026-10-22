"""Planted-fault, repeatability, and parser regressions for the hivecall eval."""
import copy
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

import eval as E

SCRIPTED = tuple(c for c in E.SCORE_CHECKS if c not in E.JUDGED_CHECKS)  # judged 12 needs Clef answers


def message(kind, time, text="", agent=None, tools=(), source=None):
    return {"type": kind, "time": time, "text": text, "agent": agent, "tools": list(tools), "source": source}


def fixture():
    brief = ("TALK-BACK: send only BUG/BLOCKED/QUESTION/STOP to parent.\n"
             "PROMISE: kind=build rows=ISC-001 result=build.log lane=Sources pace=10")
    root = [
        message("assistant", 101, agent="orchestrator", tools=[("skill", {"id": "subagent-delegation"})]),
        message("assistant", 105, agent="orchestrator", tools=[("subagent", {"agent": "build", "prompt": brief})]),
        message("assistant", 190, "Done with proof.", agent="orchestrator"),
    ]
    worker = [
        message("user", 110, "Build ISC-001", agent="build"),
        message("assistant", 120, "Working", agent="build"),
        message("assistant", 130, agent="build", tools=[("shell", {"command": "bb thread tell thr_rootthr 'QUESTION: need one detail'"})]),
        message("assistant", 180, agent="build", tools=[("write", {"path": "ledger.md", "content": "ISC-001 PASS - verified; evidence: evidence/isc-001.png"})]),
        message("assistant", 185, "BLOCKED: simulator missing for the second pass", agent="build"),
    ]
    qa = [
        message("user", 115, "Test ISC-001", agent="qa"),
        message("assistant", 160, "ISC-001 PASS: verified on device. Evidence: evidence/isc-001.png", agent="qa"),
    ]
    tree = {
        "root": {"via": "root", "parent": None, "created": 90, "agent": "orchestrator", "bb_thread": "thr_rootthr", "visible": True},
        "worker": {"via": "bb", "parent": "root", "created": 110, "agent": "build", "bb_thread": "thr_worker", "visible": True},
        "qa": {"via": "opencode", "parent": "root", "created": 115, "agent": "qa", "bb_thread": "thr_qa", "visible": True},
    }
    return {"info": {"session": "root", "run": "fixture", "loaded_by": "orchestrator", "skill_version": "test",
                      "skill_words": 10, "closed": True, "status_events": [(100, "running"), (200, "closed")],
                      "windows": [(100, 200)], "tree": tree}, "sessions": {"root": root, "worker": worker, "qa": qa}}


class EvalRegression(unittest.TestCase):
    def test_multi_file_patch_extracts_closed_status_and_tick(self):
        patch = ("*** Begin Patch\n*** Update File: .hivecall/ISA.html\n@@\n+ISC-006 PASS - ok; evidence qa/x.md\n"
                 "*** Update File: .hivecall/run.md\n@@\n-status: running\n+status: closed\n*** End Patch")
        writes = dict(E.file_writes("patch", {"patchText": patch}))
        self.assertEqual(E.STATUS.findall(writes[".hivecall/run.md"]), ["closed"])
        self.assertEqual(E.TICK.findall(writes[".hivecall/ISA.html"]), [("6", "PASS")])

    def test_worker_message_to_wrong_session_is_captured(self):
        cmd = "opencode api post /api/session/ses_typo123/prompt --data '{\"text\":\"QUESTION: which sim?\",\"delivery\":\"queue\"}'"
        (msg,) = E.worker_messages([message("assistant", 5, tools=[("shell", {"command": cmd})])])
        self.assertEqual((msg["to"], msg["ok"]), ("ses_typo123", True))

    def test_worker_messages_are_window_filtered(self):
        msgs = [message("assistant", 5, tools=[("shell", {"command": "bb thread tell thr_rootthr QUESTION: inside"})]),
                message("assistant", 25, tools=[("shell", {"command": "bb thread tell thr_rootthr RESULT: outside"})])]
        self.assertEqual(len(E.worker_messages(msgs, lambda t: t <= 10)), 1)

    def test_worker_result_post_is_not_counted_as_owner(self):
        msg = lambda t: {"text": t, "source": None}
        self.assertEqual(E.classify_inbound(msg("RESULT ISC-324 FAIL: photos shift; evidence mia11/sett1.png")), "worker-other")
        self.assertEqual(E.classify_inbound(msg("Why aren't agents actively working?")), "owner")

    def test_traffic_light_alerts_are_watchdog_not_owner(self):
        msg = lambda t: {"text": t, "source": None}
        self.assertEqual(E.classify_inbound(msg("🚦 HOST disk: only 3.0 GB free on / (<5 GB); see df -h /.")), "watchdog")
        self.assertEqual(E.alert_lines("OFF TRACK: lane A\n🚦 WATCH STALLED: no progress"), ["OFF TRACK: lane A", "🚦 WATCH STALLED: no progress"])
        for alert in ("STALL 2/3: no proof", "FREE: 2 free items", "PLAN: the run card's Plan map is out of date",
                      "DRIFT: code changed", "REANCHOR after your compaction", "UNANSWERED W3 (stall): no action"):
            self.assertEqual(E.classify_inbound(msg(alert)), "watchdog", alert)

    def test_final_report_is_read_after_the_close(self):
        run = fixture()
        info, root = run["info"], run["sessions"]["root"] + [message("assistant", 230, "Final report: 1 confirmed", agent="orchestrator")]
        inside = lambda t: 100 <= t <= 200
        self.assertEqual(E.final_report(info, root, {"root": root}, inside), "Final report: 1 confirmed")
        card = message("assistant", 199, tools=[("write", {"path": ".hivecall/run.md",
                                                        "content": "status: closed\n## Final report\nconfirmed ISC-1\n## Notes\nx"})])
        self.assertEqual(E.final_report(info, root, {"root": root + [card]}, inside).strip(), "## Final report\nconfirmed ISC-1")

    def test_redact_keeps_paths_drops_secrets(self):
        out = E.redact("see /Users/bob/app/src/components/Prompt.tsx token " + "ghp_" + "abcdefghijklmnop12")
        self.assertIn("/Users/[user]/app/src/components/Prompt.tsx", out)
        self.assertNotIn("ghp_", out)

    def test_shell_written_close_reopen_close_creates_two_windows(self):
        shell = lambda t, c: message("assistant", t, tools=[("shell", {"command": c})])
        sessions = {"root": [
            shell(100, "cat > .hivecall/run.md <<'EOF'\nstatus: running\nEOF"),
            shell(200, "python3 -c \"p='.hivecall/run.md'; s=open(p).read(); s=s.replace('status: running','status: closed',1); open(p,'w').write(s)\""),
            shell(300, "python3 -c \"p='.hivecall/run.md'; s=open(p).read(); s=s.replace('status: closed','status: running',1); open(p,'w').write(s)\""),
            shell(400, "python3 -c \"p='.hivecall/run.md'; s=open(p).read(); s=s.replace('status: running','status: closed',1); open(p,'w').write(s)\""),
            message("assistant", 500),
        ]}
        windows, events, _ = E.run_windows(sessions, {"loaded_at": 100})
        self.assertEqual(windows, [(100, 200), (300, 400)])
        self.assertEqual([s for _, s in events], ["running", "running", "closed", "closed", "running", "running", "closed"])

    def test_gate_faults_change_only_their_own_gate(self):
        baseline = fixture()
        before = E.grade(baseline)
        self.assertTrue(all(before[c]["pass"] is True for c in SCRIPTED))

        faults = {}
        x = copy.deepcopy(baseline); x["sessions"]["root"][1]["tools"][0][1]["prompt"] = x["sessions"]["root"][1]["tools"][0][1]["prompt"].replace("TALK-BACK", "TALK"); faults["1"] = x
        x = copy.deepcopy(baseline); x["sessions"]["root"][1]["tools"][0][1]["prompt"] = x["sessions"]["root"][1]["tools"][0][1]["prompt"].replace("kind=build", "kind=unknown"); faults["2"] = x
        x = copy.deepcopy(baseline); x["info"]["tree"]["worker"]["visible"] = False; faults["4"] = x
        x = copy.deepcopy(baseline); x["sessions"]["worker"][2]["tools"] = []; faults["14"] = x
        x = copy.deepcopy(baseline); x["sessions"]["qa"][-1]["text"] = "ISC-001 FAIL: no evidence"; faults["6"] = x
        x = copy.deepcopy(baseline); x["sessions"]["root"][0]["tools"].append(("read", {"path": "shots/device.png"})); faults["7"] = x
        x = copy.deepcopy(baseline); x["info"]["closed"] = False; faults["8"] = x

        # An unproven PASS tick also lowers "items proven at close"; that coupling is intended.
        expected = {"6": {"6", "10"}}
        for target, exp in faults.items():
            with self.subTest(check=target):
                after = E.grade(exp)
                changed = {c for c in SCRIPTED if before[c] != after[c]}
                self.assertEqual(changed, expected.get(target, {target}))
                self.assertFalse(after[target]["pass"])
                self.assertLess(after[target]["value"], before[target]["value"])

    def test_shell_code_edit_is_check_7_fault(self):
        self.assertEqual(E.shell_code_writes("python3 - <<'PY'\nPath('Sources/App.swift').write_text('x')\nPY"), ["Sources/App.swift"])
        self.assertEqual(E.shell_code_writes("sed -i '' 's/a/b/' src/a.ts && echo ok"), ["src/a.ts"])
        # reading, grepping or running a code file is not an edit
        for cmd in ['grep -n "x" app/_layout.tsx | head; ls repro 2>/dev/null',
                    "python3 .hivecall/watch.py > /tmp/watch.log 2>&1",
                    "echo 'diff in tests/app-shell.test.ts is expected' > /tmp/msg.json"]:
            self.assertEqual(E.shell_code_writes(cmd), [], cmd)
        x = copy.deepcopy(fixture())
        x["sessions"]["root"][0]["tools"].append(("shell", {"command": "python3 - <<'PY'\nPath('Sources/App.swift').write_text('x')\nPY"}))
        before, after = E.grade(fixture()), E.grade(x)
        self.assertEqual({c for c in SCRIPTED if before[c] != after[c]}, {"7"})

    def test_wrong_parent_target_moves_context_check_5_only(self):
        x = copy.deepcopy(fixture())
        x["sessions"]["worker"][2]["tools"][0][1]["command"] = "bb thread tell thr_typo123 'QUESTION: need one detail'"
        before, after = E.grade(fixture()), E.grade(x)
        self.assertEqual({c for c in SCRIPTED if before[c] != after[c]}, set())
        self.assertLess(after["5"]["value"], before["5"]["value"])

    def test_check_6_requires_qa_final_same_item_and_evidence_path(self):
        base = fixture()
        variants = []
        x = copy.deepcopy(base); x["info"]["tree"]["qa"]["agent"] = "reviewer"; variants.append(x)
        x = copy.deepcopy(base); x["sessions"]["qa"][-1]["text"] = "ISC-002 PASS. Evidence: evidence/isc-001.png"; variants.append(x)
        x = copy.deepcopy(base); x["sessions"]["qa"][-1]["text"] = "ISC-001 PASS. Evidence: verified on device"; variants.append(x)
        for exp in variants:
            self.assertFalse(E.grade(exp)["6"]["pass"])

    def test_unparseable_ticks_are_not_a_check_6_pass(self):
        x = copy.deepcopy(fixture())
        x["sessions"]["worker"][3]["tools"][0][1]["content"] = "The ledger was updated but no verdict was written."
        result = E.grade(x)["6"]
        self.assertIsNone(result["pass"])
        self.assertIn("no PASS ticks parsed", result["note"])

    def test_context_delegate_before_skill_load_is_not_a_gate(self):
        x = copy.deepcopy(fixture())
        x["sessions"]["root"][0]["tools"] = []
        result = E.grade(x)
        self.assertFalse(result["3"]["value"])
        self.assertIsNone(result["3"]["pass"])
        self.assertTrue(all(result[c]["pass"] is True for c in SCRIPTED))

    def test_repeat_grading_and_post_close_noise_leave_gate_values_identical(self):
        exp = fixture()
        first, again = E.grade(exp), E.grade(exp)
        self.assertEqual(first, again)
        noisy = copy.deepcopy(exp)
        noisy["info"]["tree"]["late"] = {"via": "bb", "parent": "root", "created": 201, "agent": "build", "bb_thread": "thr_late", "visible": False}
        noisy["sessions"]["late"] = [message("assistant", 250, "outside-window", agent="build",
                                                 tools=[("shell", {"command": "bb thread tell thr_typo RESULT: wrong"})])]
        noisy["sessions"]["root"].append(message("assistant", 260, agent="build",
                                                  tools=[("subagent", {"agent": "build", "prompt": "No TALK-BACK\nPROMISE: invalid"})]))
        noisy["sessions"]["root"].append(message("assistant", 270, agent="orchestrator",
                                                  tools=[("read", {"path": "late/screenshot.png"})]))
        after = E.grade(noisy)
        self.assertEqual({c: first[c] for c in SCRIPTED}, {c: after[c] for c in SCRIPTED})

    def test_tester_result_row_mentioning_the_ledger_is_not_a_tick(self):
        row = "cat >> .hivecall/verification/qa-core.md <<'EOF'\n| ISC-3 | PASS | see ISA.html criteria | log.txt |\nEOF"
        self.assertFalse(E.ledger_shell_write(row))
        loop = "python3 - <<'EOF'\np='ISA.html'; s=open(p).read()\nfor i in ['1','6']:\n  s=s.replace(f'ISC-{i}', 'x')\nopen(p,'w').write(s)\nEOF"
        self.assertTrue(E.ledger_shell_write(loop))
        self.assertTrue(E.ledger_shell_write("sed -i '' 's/a/b/' .hivecall/checklist.html"))

    def test_ledger_at_end_fills_ticks_the_trace_missed(self):
        x = copy.deepcopy(fixture())
        x["info"]["ledger"] = {"total": 2, "latest": {"1": "PASS", "2": "FAIL"}}
        result = E.grade(x)
        self.assertEqual(result["10"]["n"], 2)
        self.assertEqual(result["10"]["value"], 0.5)

    def test_paused_run_with_final_report_counts_as_closed(self):
        x = copy.deepcopy(fixture())
        x["info"].update(closed=False, status_events=[(100, "running"), (200, "waiting-owner")])
        self.assertFalse(E.grade(x)["8"]["pass"])
        x["info"]["final_report_written"] = True
        self.assertTrue(E.grade(x)["8"]["pass"])

    def test_reread_after_compaction_before_next_hand_off(self):
        x = copy.deepcopy(fixture())
        root = x["sessions"]["root"]
        root.insert(1, message("assistant", 102, agent="orchestrator", tools=[("compress", {})]))
        self.assertEqual(E.grade(x)["19"]["value"], 0.0)  # hand-off at 105 came first
        root.insert(2, message("assistant", 103, agent="orchestrator", tools=[("read", {"path": "/s/hivecall/HOW-TO-WORK.md"})]))
        self.assertEqual(E.grade(x)["19"]["value"], 1.0)

    def test_alert_needs_answer_and_action_within_ten_minutes(self):
        x = copy.deepcopy(fixture())
        x["info"]["windows"] = [(100, 2_000_000)]
        root = x["sessions"]["root"]
        root.append(message("user", 1000, "STALL 1/3: no proof for 10 min. Ask: why? (alert W1)"))
        self.assertEqual(E.grade(x)["20"]["value"], 0.0)
        root.append(message("assistant", 200_000, agent="orchestrator",
                            tools=[("edit", {"path": ".hivecall/run.md", "newString": "ANSWER W1: split ISC-1 — thr_new"}),
                                   ("shell", {"command": "bb thread spawn --parent-self --title split"})]))
        self.assertEqual(E.grade(x)["20"]["value"], 1.0)

    def test_pass_later_broken_is_a_downhill_step(self):
        x = copy.deepcopy(fixture())
        x["info"]["ledger"] = {"total": 1, "latest": {"1": "FAIL"}}
        result = E.grade(x)["22"]
        self.assertEqual(result["value"], 1)
        self.assertFalse(result["pass"])

    def test_older_ledger_snapshot_never_overrides_a_newer_trace_verdict(self):
        x = copy.deepcopy(fixture())
        x["info"]["ledger"] = {"total": 1, "at": 150, "latest": {"1": "FAIL"}}  # trace PASS is at 180
        self.assertEqual(E.grade(x)["10"]["value"], 1.0)

    def test_rewritten_old_verdict_lines_are_not_new_events(self):
        x = copy.deepcopy(fixture())
        write = lambda t, text: message("assistant", t, agent="orchestrator", tools=[("write", {"path": "ISA.html", "content": text})])
        x["sessions"]["root"][1:1] = [write(150, "ISC-002: FAIL - old"), write(170, "ISC-002: FAIL - old\nISC-002: PASS - fixed"),
                                      write(175, "ISC-002: FAIL - old\nISC-002: PASS - fixed")]
        self.assertEqual(E.grade(x)["22"]["value"], 0)

    def test_answer_outside_the_run_card_does_not_count(self):
        x = copy.deepcopy(fixture())
        x["info"]["windows"] = [(100, 2_000_000)]
        x["sessions"]["root"] += [message("user", 1000, "FREE: 2 free items (alert W1)"),
                                  message("assistant", 2000, agent="orchestrator",
                                          tools=[("shell", {"command": "bb thread spawn --parent-self --prompt 'ANSWER W1: go'"})])]
        self.assertEqual(E.grade(x)["20"]["value"], 0.0)

    def test_orchestrator_switching_agent_mid_run_is_reported(self):
        x = copy.deepcopy(fixture())
        self.assertEqual(E.grade(x)["24"]["value"], 1.0)
        x["sessions"]["root"][-1]["agent"] = "build"
        result = E.grade(x)["24"]
        self.assertFalse(result["pass"])
        self.assertIn("switched to build", result["note"])

    def test_orchestrator_ledger_tool_scripts_are_not_code_edits(self):
        x = copy.deepcopy(fixture())
        x["sessions"]["root"].insert(1, message("assistant", 102, agent="orchestrator",
                                                tools=[("shell", {"command": "cat > .lanes/tick.py <<'EOF'\nprint(1)\nEOF"})]))
        self.assertTrue(E.grade(x)["7"]["pass"])
        x["sessions"]["root"].insert(1, message("assistant", 103, agent="orchestrator",
                                                tools=[("write", {"path": "js/app.js", "content": "x"})]))
        self.assertFalse(E.grade(x)["7"]["pass"])

    def test_saved_ledger_copy_is_used_once_the_run_folder_is_gone(self):
        with TemporaryDirectory() as td:
            (Path(td) / "ledger-at-end.html").write_text(
                '<section id="criteria"><ul><li id="ISC-1"><input type="checkbox" disabled checked> ISC-1: one</li>'
                '<li id="ISC-2"><input type="checkbox" disabled> ISC-2: two</li></ul></section>'
                '<section id="verification"><ul><li>ISC-1: PASS - ok</li></ul></section>')
            snap = E.ledger_at_end(str(Path(td) / "deleted-run"), 1000, Path(td))
            self.assertEqual(snap.get("source"), "saved copy")
            self.assertEqual(snap.get("latest", {}).get("1"), "PASS")

    def test_freeze_snapshot_is_complete_and_guarded(self):
        with TemporaryDirectory() as td, patch.object(E, "OUT", Path(td)):
            row = {"run": "fixture", "eval_version": E.EVAL_VERSION, "skill_version": "test",
                   "skill_commit": "working-tree", "skill_fingerprint": "abc123",
                   "checks": {"1": {"value": 1.0, "pass": True, "note": "1/1 briefs"}, "12": {}, "13": {}, "16": {}, "18": {}}}
            (Path(td) / "results.jsonl").write_text(json.dumps(row) + "\n")
            path = E.freeze_baseline()
            snapshot = json.loads(path.read_text())
            self.assertEqual(snapshot["eval_version"], E.EVAL_VERSION)
            self.assertEqual(snapshot["runs"][0]["skill_fingerprint"], "abc123")
            self.assertEqual(snapshot["runs"][0]["checks"]["1"], row["checks"]["1"])
            self.assertEqual(snapshot["runs"][0]["score"], {"score": 100, "used": 1})
            with self.assertRaises(SystemExit):
                E.freeze_baseline()
            (Path(td) / "results.jsonl").write_text(json.dumps({**row, "eval_version": "1.0"}) + "\n")
            with self.assertRaises(SystemExit):
                E.freeze_baseline(force=True)


if __name__ == "__main__":
    unittest.main()
