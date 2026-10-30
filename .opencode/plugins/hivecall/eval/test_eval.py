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
    def test_discovery_backing_and_code_review_not_proof(self):
        for verdict in ("APPROVE_PLAN", "SELECTED", "APPROVE_CODE"):
            with self.subTest(verdict=verdict):
                run = fixture()
                run["info"]["ledger"] = {"discovery": ["1"]}
                run["info"]["tree"]["qa"]["agent"] = "reviewer"
                run["sessions"]["qa"] = [message("user", 115, "PROMISE: kind=helper rows=ISC-001,ISC-002 result=- lane=-", agent="reviewer"),
                                          message("assistant", 160, f"- Status: `{verdict}`", agent="reviewer")]
                grade = E.grade(run)
                self.assertEqual(grade["6"]["pass"], verdict != "APPROVE_CODE")
                self.assertEqual(grade["10"]["pass"], verdict != "APPROVE_CODE")
        run = fixture()
        run["info"]["ledger"] = {"discovery": ["1"]}
        run["sessions"]["qa"][0]["text"] = "PROMISE: kind=helper rows=ISC-001 result=- lane=-"
        run["sessions"]["qa"][-1]["text"] = "ISC-001 REPRODUCED: evidence: evidence/isc-001.png"
        self.assertTrue(E.grade(run)["6"]["pass"])
        run["sessions"]["qa"][-1]["text"] = "ISC-001 NOT_REPRODUCED: evidence: evidence/isc-001.png"
        self.assertFalse(E.grade(run)["6"]["pass"])

    def test_discovery_requires_promised_rows_and_bare_result_covers_both(self):
        run = fixture()
        run["sessions"]["qa"][0]["text"] = "slice=ISC-001\nPROMISE: kind=helper rows=- result=- lane=-"
        run["sessions"]["qa"][-1]["text"] = "Result: REPRODUCED\nEvidence: evidence/isc-001.png"
        self.assertFalse(E.grade(run)["6"]["pass"])
        run["sessions"]["qa"][0]["text"] = "PROMISE: kind=helper rows=ISC-001,ISC-002 result=- lane=-"
        run["sessions"]["worker"][3]["tools"][0][1]["content"] += "\nISC-002 PASS - verified; evidence: evidence/isc-002.png"
        run["info"]["ledger"] = {"discovery": ["1", "2"]}
        self.assertTrue(E.grade(run)["6"]["pass"])
        run["sessions"]["qa"][-1]["text"] += "\nISC-002: NOT_REPRODUCED"
        self.assertFalse(E.grade(run)["6"]["pass"])
        run["sessions"]["qa"][-1]["text"] = "Risks: ISC-001 bug reproduced after restore. evidence: evidence/isc-001.png"
        self.assertFalse(E.grade(run)["6"]["pass"])  # prose, not a REPRODUCED verdict
        run["sessions"]["qa"][-1]["text"] = "- Result: `REPRODUCED`\nEvidence: evidence/isc-001.png"
        self.assertTrue(E.grade(run)["6"]["pass"])
        run["sessions"]["qa"][0]["text"] = "Test ISC-002"
        self.assertFalse(E.grade(run)["6"]["pass"])

    def test_discovery_scope_and_negative_decisions(self):
        run = fixture()
        run["info"]["ledger"] = {"discovery": ["1"]}
        run["info"]["tree"]["qa"]["agent"] = "reviewer"
        run["sessions"]["qa"] = [message("user", 115, "PROMISE: kind=helper rows=ISC-001 result=- lane=-", agent="reviewer"),
                                  message("assistant", 160, "Decision: REVISE_PLAN\nEarlier APPROVE_PLAN", agent="reviewer")]
        self.assertFalse(E.grade(run)["6"]["pass"])
        run["sessions"]["qa"][-1]["text"] = "Decision: APPROVE_PLAN\nISC-001: ASK_USER"
        self.assertFalse(E.grade(run)["6"]["pass"])
        run["sessions"]["qa"][-1]["text"] = "Decision: APPROVE_PLAN"
        run["info"]["ledger"] = {"discovery": []}
        self.assertFalse(E.grade(run)["6"]["pass"])
        run = fixture()
        run["info"]["ledger"] = {"discovery": ["1"]}
        run["sessions"]["qa"][0]["text"] = "Test ISC-001\nPROMISE: kind=helper rows=ISC-002 result=- lane=-"
        run["sessions"]["qa"][-1]["text"] = "ISC-001 REPRODUCED: evidence: evidence/isc-001.png"
        self.assertFalse(E.grade(run)["6"]["pass"])

    def test_discovery_missing_metadata_fails_closed(self):
        for role, verdict in (("reviewer", "Decision: APPROVE_PLAN"), ("qa", "Result: REPRODUCED\nEvidence: evidence/isc-001.png")):
            with self.subTest(role=role):
                run = fixture()
                run["info"]["tree"]["qa"]["agent"] = role
                run["sessions"]["qa"] = [message("user", 115, "PROMISE: kind=helper rows=ISC-001 result=- lane=-", agent=role),
                                          message("assistant", 160, verdict, agent=role)]
                self.assertFalse(E.grade(run)["6"]["pass"])

    def test_bare_negative_vetoes_discovery_but_not_build_pass(self):
        for verdict in ("NOT_REPRODUCED", "BLOCKED"):
            with self.subTest(verdict=verdict):
                run = fixture()
                run["info"]["ledger"] = {"discovery": ["1"]}
                run["sessions"]["qa"][0]["text"] = "PROMISE: kind=helper rows=ISC-001 result=- lane=-"
                run["sessions"]["qa"][-1] = message("assistant", 160, f"Result: {verdict}", agent="qa", tools=[("write", {"path": "evidence/result.md", "content": "ISC-001 REPRODUCED"})])
                self.assertFalse(E.grade(run)["6"]["pass"])
                run["sessions"]["qa"][-1]["tools"][0][1]["content"] = "ISC-001 PASS"
                self.assertFalse(E.grade(run)["6"]["pass"])  # Discovery: the final negative wins, as in the plugin
                run["info"]["ledger"] = {"discovery": []}
                self.assertTrue(E.grade(run)["6"]["pass"])  # build items keep today's PASS-row backing

    def test_qa_bare_pass_backs_promised_discovery_rows_unless_vetoed(self):
        run = fixture()
        run["info"]["ledger"] = {"discovery": ["1", "2"]}
        run["sessions"]["worker"][3]["tools"][0][1]["content"] += "\nISC-002 PASS - verified"
        run["sessions"]["qa"][0]["text"] = "PROMISE: kind=helper rows=ISC-001,ISC-002 result=- lane=-"
        run["sessions"]["qa"][-1] = message("assistant", 160, "Result: PASS", agent="qa", tools=[("write", {"path": "evidence/result.md", "content": "checked"})])
        self.assertTrue(E.grade(run)["6"]["pass"])
        for veto in ("Result: PASS\nResult: FAIL", "Result: PASS; BLOCKED", "Result: PASS\nISC-002 FAIL"):
            with self.subTest(veto=veto):
                run["sessions"]["qa"][-1]["text"] = veto
                self.assertFalse(E.grade(run)["6"]["pass"])
        run["sessions"]["qa"][0]["text"] = "PROMISE: kind=helper rows=ISC-001 result=- lane=-"  # single item: file_pass/row_pass paths
        for veto in ("PASS\nFAIL", "PASS\nBLOCKED"):
            with self.subTest(single=veto):
                run["sessions"]["qa"][-1]["text"] = veto
                self.assertFalse(E.grade(run)["6"]["pass"])
        run["sessions"]["qa"][0]["text"] = "PROMISE: kind=helper rows=ISC-001,ISC-002 result=- lane=-"
        run["sessions"]["qa"][-1]["text"] = "Result: PASS"
        run["info"]["ledger"] = {"discovery": []}  # build items keep today's rules: bare PASS on a generic file is not enough
        self.assertFalse(E.grade(run)["6"]["pass"])

    def test_reviewer_overall_negative_vetoes_discovery(self):
        for text in ("Decision: APPROVE_PLAN\nDecision: REVISE_PLAN", "Decision: APPROVE_PLAN; ASK_USER"):
            with self.subTest(text=text):
                run = fixture()
                run["info"]["ledger"] = {"discovery": ["1"]}
                run["info"]["tree"]["qa"]["agent"] = "reviewer"
                run["sessions"]["qa"] = [message("user", 115, "PROMISE: kind=helper rows=ISC-001 result=- lane=-", agent="reviewer"),
                                          message("assistant", 160, text, agent="reviewer")]
                self.assertFalse(E.grade(run)["6"]["pass"])

    def test_promise_parser_matches_plugin_fixtures(self):
        fixtures = json.loads((E.SKILL / "test" / "promise-parity.json").read_text())
        for row in fixtures:
            with self.subTest(text=row["text"]):
                parsed = E.parse_promise(row["text"])
                if row["valid"] is None:
                    self.assertIsNone(parsed)
                    continue
                self.assertIsNotNone(parsed)
                self.assertEqual(parsed["valid"], row["valid"])
                self.assertEqual(parsed["kind"], row["kind"])
                self.assertEqual(sorted(parsed["rows"]), row["rows"])
                self.assertEqual(parsed["pace"], row["pace"])

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

    def test_bb_helper_running_as_another_agent_is_reported_and_still_a_tester(self):
        x = copy.deepcopy(fixture())
        self.assertIsNone(E.grade(x)["25"]["value"])  # no brief names an agent
        x["info"]["tree"]["qa"].update(via="bb", agent="build")
        x["sessions"]["qa"][0]["text"] = "agent: qa\n\nYou are Cy (qa). Test ISC-001"
        x["sessions"]["qa"][1]["agent"] = "build"
        result = E.grade(x)
        self.assertEqual(result["25"]["value"], 0.0)
        self.assertFalse(result["25"]["pass"])
        self.assertIn("briefed qa, ran build 1", result["25"]["note"])
        self.assertTrue(result["6"]["pass"])  # BB cannot pin the agent; the brief's role makes it the tester
        x["info"]["tree"]["qa"]["via"] = "opencode"  # a subagent call could have named qa, so build is not a tester
        self.assertFalse(E.grade(x)["6"]["pass"])

    def bb_reviewer_helper(self, *turn_agents):
        x = copy.deepcopy(fixture())
        x["info"]["tree"]["qa"].update(via="bb", agent="reviewer")  # session metadata says reviewer
        x["sessions"]["qa"] = [message("user", 115, "agent: reviewer\n\nYou are Rae (reviewer). Review ISC-001")] + [
            message("assistant", 140 + i, "APPROVE_CODE" if i == len(turn_agents) - 1 else "reading", agent=a)
            for i, a in enumerate(turn_agents)]
        return E.grade(x)["25"]

    def test_helper_judged_on_its_turns_not_session_agent(self):
        self.assertEqual(self.bb_reviewer_helper("reviewer", "reviewer")["note"], "1/1 helpers ran as briefed")
        late = self.bb_reviewer_helper("build", "reviewer", "reviewer")  # pinned after turn 1 already ran as build
        self.assertFalse(late["pass"])
        self.assertIn("briefed reviewer, ran build+reviewer 1", late["note"])
        all_build = self.bb_reviewer_helper("build", "build")
        self.assertFalse(all_build["pass"])
        self.assertIn("briefed reviewer, ran build 1", all_build["note"])

    def test_subagent_call_agent_is_the_briefed_role(self):
        x = copy.deepcopy(fixture())
        prompt = x["sessions"]["root"][1]["tools"][0][1]["prompt"]
        x["sessions"]["worker"][0]["text"] = E.SUBAGENT_PREAMBLE + "\n" + prompt
        x["info"]["tree"]["worker"]["via"] = "opencode"
        self.assertEqual(E.grade(x)["25"]["note"], "1/1 helpers ran as briefed")
        x["sessions"]["root"][1]["tools"][0][1]["agent"] = "reviewer"
        self.assertIn("briefed reviewer, ran build 1", E.grade(x)["25"]["note"])

    def test_prompt_file_spawns_are_read_per_loop_item(self):
        loop = "for k in rev-a qa-a; do bb thread spawn --parent-self --prompt-file .lanes/brief-$k.md --json; done"
        msgs = [message("assistant", 150, agent="orchestrator", tools=[("shell", {"command": loop}),
                                                                       ("shell", {"command": "bb thread spawn --help"})])]
        self.assertEqual(E.prompt_file_paths(loop), [".lanes/brief-rev-a.md", ".lanes/brief-qa-a.md"])
        self.assertEqual([b["text"] for b in E.briefs_of(msgs, lambda t: True)], [loop])  # files not saved: old behavior
        with TemporaryDirectory() as td:
            (Path(td) / ".lanes").mkdir()
            for k in ("rev-a", "qa-a"):
                (Path(td) / ".lanes" / f"brief-{k}.md").write_text(f"TALK-BACK: {k}\nPROMISE: kind=helper rows=ISC-1 result=- lane=-")
            files = E.saved_prompt_files(msgs, td, {})
        self.assertEqual(sorted(files), [".lanes/brief-qa-a.md", ".lanes/brief-rev-a.md"])
        briefs = E.briefs_of(msgs, lambda t: True, files)
        self.assertEqual([b["text"].splitlines()[0] for b in briefs], ["TALK-BACK: rev-a", "TALK-BACK: qa-a"])
        self.assertEqual(E.saved_prompt_files(msgs, str(Path(td) / "gone"), files), files)  # saved copy survives

    def test_verdict_lines_outside_the_verification_list_are_read(self):
        with TemporaryDirectory() as td:
            snap = Path(td) / "ledger-at-end.html"
            snap.write_text('<section id="criteria"><ul><li id="ISC-1"><input type="checkbox" disabled checked> ISC-1: one</li>'
                            '<li id="ISC-2"><input type="checkbox" disabled checked> ISC-2: two</li>'
                            '<li>ISC-2: PASS - qa ok; commit abc1234; evidence qa.md</li>'
                            '<li>ISC-1: FAIL - stray older line</li></ul></section>'
                            '<section id="verification"><ul><li>ISC-1: PASS - ok</li></ul></section>')
            latest = E.ledger_summary(snap, Path(td), "working file", 1000, "ISA.html")["latest"]
        self.assertEqual(latest, {"1": "PASS", "2": "PASS"})  # the verification list still wins for ISC-1

    def test_list_prints_a_run_without_a_title(self):
        run = {"index": 1, "run": "2026-10-23-abcdef", "session": "ses_abcdef", "loaded_at": 0, "loaded_by": "build", "title": None}
        with TemporaryDirectory() as td, patch.object(E, "OUT", Path(td)), patch.object(E, "ro", lambda _p: None), \
                patch.object(E, "find_runs", lambda _oc: [run]), patch("sys.argv", ["eval.py", "--list"]), \
                patch("builtins.print") as out:
            E.main()
        self.assertIn("2026-10-23-abcdef", out.call_args[0][0])

    def test_regrade_skips_a_run_whose_skill_matches_no_version_and_still_builds_the_dashboard(self):
        run = {"index": 1, "run": "2026-10-23-probe1", "session": "ses_probe1", "loaded_at": 0, "loaded_by": "build", "title": "p",
               "directory": None, "_body": "not the hivecall skill"}
        with TemporaryDirectory() as td, patch.object(E, "OUT", Path(td)), patch.object(E, "ro", lambda _p: None), \
                patch.object(E, "find_runs", lambda _oc: [run]), patch("sys.argv", ["eval.py", "--regrade"]), \
                patch.object(E, "skill_version", lambda _b: {"skill_version": "~unknown", "skill_commit": "unknown", "match": 0}), \
                patch.object(E, "dashboard", lambda: Path(td) / "dashboard.html"), patch("builtins.print") as out:
            E.main()
        lines = [c[0][0] for c in out.call_args_list]
        self.assertEqual(lines[0], "skipped 2026-10-23-probe1: its loaded skill body matches no SKILL.md version")
        self.assertTrue(lines[-1].startswith("0 run(s) graded"))

    def test_paused_run_with_progress_report_counts_as_closed(self):
        card = "status: waiting-owner\n\n## Progress report\n{}\n## Lessons\n"
        write = lambda body: {"root": [message("assistant", 150, agent="orchestrator", tools=[("write", {"path": "/r/.hivecall/run.md", "content": card.format(body)})])]}
        self.assertFalse(E.final_report_written(write(""), None))  # an empty heading is not a report
        self.assertTrue(E.final_report_written(write("ISC-1 done; ISC-2 waits on the owner's API key."), None))

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



class GrowthFixtures(unittest.TestCase):
    def test_frozen_growth_records(self):
        rows = json.loads((E.HERE / "fixtures/growth.json").read_text())
        for row in rows:
            with self.subTest(row=row["name"]):
                with TemporaryDirectory() as td:
                    path = Path(td) / "ledger.html"
                    items = '<li id="ISC-1"><input type="checkbox" disabled data-status="parked"> ISC-1: original</li><li id="ISC-2"><input type="checkbox" disabled checked> ISC-2: replacement</li>'
                    path.write_text('<h3>Criteria</h3><ul class="isc">' + items + '</ul><section id="verification"><ul>' + ''.join('<li>' + r + '</li>' for r in row['records']) + '<li>ISC-2: PASS - proven; evidence proof/result.md</li></ul></section>')
                    if row['name'] == 'approved replacement':
                        self.assertTrue(E.parse_isa(str(path), td)['done'])
                    growth = E.ledger_summary(path, Path(td), 'fixture', 1, 'ledger.html')['growth']
                    for key in ('added', 'incomplete', 'chained', 'superseded'):
                        self.assertEqual(growth[key], row[key])

if __name__ == "__main__":
    unittest.main()
