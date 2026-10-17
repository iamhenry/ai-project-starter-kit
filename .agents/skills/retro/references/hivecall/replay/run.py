#!/usr/bin/env python3
"""Baseline and blind replay evaluation for the hivecall weekly loop."""
import argparse
import datetime as dt
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import random
import re
import subprocess
import sys
import tempfile
import urllib.error
import urllib.request

ROOT = Path(__file__).resolve().parents[6]
HERE = Path(__file__).resolve().parent
HIVECALL = ROOT / ".agents/skills/retro/references/hivecall"
DATASET = HIVECALL / "evals/dataset.jsonl"
RESULTS = HIVECALL / "evals/results.jsonl"
CURRENT_SKILL = ROOT / ".agents/skills/hivecall/SKILL.md"
sys.path.insert(0, str(HIVECALL / "scripts"))
sys.path.insert(0, str(HIVECALL / "gate"))
from redact import redact, redact_value  # noqa: E402
import judge as judge_client  # noqa: E402
import b3 as b3_replay  # noqa: E402

RUNTIME = None


class MaxCallsReached(RuntimeError):
    pass


class CallRuntime:
    """Atomic, payload-keyed checkpoints and per-run call visibility."""

    def __init__(self, cache_dir, max_calls=None):
        self.cache_dir = Path(cache_dir).expanduser()
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.log_path = self.cache_dir / "replay.log"
        self.max_calls = max_calls
        self.estimates = {}
        self.stage_calls = {}
        self.cache_hits = 0
        self.cache_writes = 0
        self.new_calls = 0
        self.processed_calls = 0

    def emit(self, message):
        line = f"{dt.datetime.now(dt.timezone.utc).isoformat()} {message}"
        print(message, file=sys.stderr, flush=True)
        with self.log_path.open("a", encoding="utf-8") as log:
            log.write(line + "\n")

    def set_estimates(self, estimates):
        self.estimates = dict(estimates)
        total = sum(self.estimates.values())
        self.emit("Call estimate (upper bound; cache hits reduce new calls): " + "; ".join(
            f"{stage} ≤{count}" for stage, count in self.estimates.items()) + f"; total ≤{total}")

    def status(self, reason):
        remaining = max(1, sum(self.estimates.values()) - self.processed_calls)
        return (f"BLOCKED: {reason} ({self.cache_hits + self.cache_writes} calls cached, "
                f"{remaining} estimated remaining)")

    def call(self, stage, model, payload, invoke, identity=""):
        encoded = json.dumps({"model": model, "payload": payload, "identity": identity}, ensure_ascii=False,
                             sort_keys=True, separators=(",", ":")).encode("utf-8")
        key = hashlib.sha256(encoded).hexdigest()
        path = self.cache_dir / f"{key}.json"
        try:
            saved = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(saved, dict) and saved.get("key") == key and "result" in saved:
                self.cache_hits += 1
                self.processed_calls += 1
                self.stage_calls[stage] = self.stage_calls.get(stage, 0) + 1
                total = self.estimates.get(stage, "?")
                self.emit(f"[{stage}] {self.stage_calls[stage]}/{total} cache hit {key[:12]}")
                return saved["result"]
        except (OSError, ValueError):
            pass

        if self.max_calls is not None and self.new_calls >= self.max_calls:
            message = self.status("max-calls reached")
            self.emit(message)
            raise MaxCallsReached(message)

        self.stage_calls[stage] = self.stage_calls.get(stage, 0) + 1
        total = self.estimates.get(stage, "?")
        self.emit(f"[{stage}] {self.stage_calls[stage]}/{total} request {key[:12]}")
        self.new_calls += 1
        result = invoke()
        saved = json.dumps({"key": key, "model": model, "result": result},
                           ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        fd, temporary = tempfile.mkstemp(prefix=".checkpoint-", suffix=".tmp", dir=self.cache_dir)
        try:
            with os.fdopen(fd, "wb") as out:
                out.write(saved)
                out.flush()
                os.fsync(out.fileno())
            os.chmod(temporary, 0o600)
            os.replace(temporary, path)
        finally:
            if os.path.exists(temporary):
                os.unlink(temporary)
        self.cache_writes += 1
        self.processed_calls += 1
        return result


def configure_call_estimates(estimates):
    if RUNTIME is not None:
        RUNTIME.set_estimates(estimates)


def blocked_message(reason):
    return RUNTIME.status(reason) if RUNTIME is not None else f"BLOCKED: {reason}"

BEHAVIORS = {
    1: "Every checklist item is finished or explicitly parked with a reason.",
    2: "Never tick an item without item-specific, independent proof.",
    3: "Do not leave work open and go quiet; keep making useful progress.",
    4: "Run independent work in parallel without overlapping ownership or files.",
    5: "Treat watchdog alerts accurately: act on real problems, ignore false alarms, and do not miss stalls.",
    6: "Give workers bounded briefs and leave clean, useful reports.",
    7: "Use reasonable time and cost (measured at run level, not by replay).",
}
SURE = 0.8
ALERT_Q = "https://ollama.com/v1/systemone"
GAP_SIGNAL = re.compile(r"\b(gap|quiet|idle|silence|silent|elapsed|since|last activity|no activity|no message|no evidence)\b", re.I)
ELAPSED_TIME = re.compile(r"\b(?:\d+\s*(?:minutes?|mins?|hours?|hrs?)|\d{1,2}:\d{2}|\d+\s*days?)\b", re.I)
OPEN_WORK = re.compile(r"\b(open|in progress|not started|stuck|remaining|unfinished|blocked)\b", re.I)


def read_records(path):
    records = []
    for line_no, line in enumerate(Path(path).read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"invalid JSONL at {path}:{line_no}") from exc
        if row.get("recordType") not in ("run", "runUpdate"):
            continue
        records.append(row)
    return records


def moments_by_run(records):
    runs = {}
    for record in records:
        run_id = record.get("runId")
        if not run_id:
            continue
        run = runs.setdefault(run_id, {"week": record.get("week"), "moments": {}, "workers": []})
        run["week"] = record.get("week") or run["week"]
        run["workers"].extend(record.get("workers", []))
        for moment in record.get("moments", []):
            key = moment.get("momentId") or json.dumps(
                [moment.get("eventId"), moment.get("behavior"), moment.get("itemId")], sort_keys=True)
            run["moments"][key] = moment
    return runs


def all_moments(records):
    runs = moments_by_run(records)
    return [dict(m, week=m.get("week") or r["week"], workers=r["workers"])
            for r in runs.values() for m in r["moments"].values()]


def replayable_moment(moment):
    behavior = moment.get("behavior")
    if behavior == 7:  # Run-level measurements are descriptive, never replayed.
        return False
    if behavior == 3:
        check = moment.get("fixedCheck") or {}
        action = moment.get("actualNextAction") or {}
        workers = check.get("liveWorkerCount")
        return (moment.get("replayAnchor") == "b3_pre_final_message"
                and action.get("kind") == "agentMessage"
                and action.get("eventType") == "item/completed"
                and check.get("anchor") == "before-final-orchestrator-message"
                and check.get("label") == "open"
                and isinstance(workers, int) and workers >= 0
                and isinstance(check.get("gapMinutes"), (int, float))
                and check["gapMinutes"] > 30)
    if behavior in (4, 6):
        action = moment.get("actualNextAction") or {}
        return action.get("eventType") == "item/started" and action.get("status") == "pending"
    return behavior in (1, 2, 5)


def baseline_moment(moment):
    """Select observed trace outcomes; B3 may use evaluator-only gap metadata."""
    behavior = moment.get("behavior")
    if behavior == 3:
        gap = (moment.get("fixedCheck") or {}).get("gapMinutes")
        return isinstance(gap, (int, float)) and gap >= 30
    if behavior in (4, 6):
        action = moment.get("actualNextAction") or {}
        return action.get("eventType") == "item/started" and action.get("status") == "pending"
    return behavior in (1, 2, 5)


def validate_excluded_runs(ids):
    if len(ids) != len(set(ids)):
        raise SystemExit("do not repeat --exclude-run-id values")


def fixed_label(moment):
    check = moment.get("fixedCheck") or {}
    return str(check.get("label") or "").lower()


def action_text(moment):
    action = moment.get("actualNextAction") or {}
    return str(action.get("text") or "")


def claims_completion(text):
    if re.search(r"\b(?:only after|once|when|unless|after|if)\b.{0,120}\b(?:proof|qa|test|evidence)\b", text, re.I | re.S):
        return False
    if re.search(r"\b(do not|don't|never|not|should not|shouldn't|without)\s+(?:yet\s+)?(?:tick|mark|pass|complete|finish)", text, re.I):
        return False
    return bool(re.search(r"\b(tick|ticked|pass|passed|complete|completed|done)\b", text, re.I))


def rule_label(moment, behavior, candidate=None):
    """Return a rule-backed PASS/FAIL only where the trace schema supports it."""
    label = fixed_label(moment)
    text = action_text(moment) if candidate is None else candidate
    if behavior == 1:
        if label in ("tick", "pass", "done", "complete", "completed"):
            return "PASS"
        if label in ("park", "parked"):
            return "PASS" if re.search(r"\b(because|reason|waiting|until|blocked by|owner-only|unblock)\b", text, re.I) else "FAIL"
        if label in ("fail", "blocked", "retry"):
            return "FAIL"
    elif behavior == 2:
        if label == "proof_present":
            return "PASS"
        if label == "proof_not_detected":
            if candidate is None:
                return "FAIL"
            # A candidate cannot claim the item is complete when the trace has no proof.
            return "FAIL" if claims_completion(text) else "PASS"
    elif behavior == 3:
        if moment.get("replayAnchor") == "b3_pre_final_message":
            return None
        if label == "open":
            return "FAIL"
        if label == "closed":
            return "PASS"
    elif behavior == 5:
        if label == "no_follow_up":
            return "FAIL"
    elif behavior == 6:
        if label == "task_bounds_present":
            return "PASS"
        if label == "task_bounds_not_detected":
            return "FAIL"
    return None


def clef_key():
    key = os.environ.get("OLLAMA_API_KEY")
    if key:
        return key
    try:
        return json.loads((Path.home() / ".local/share/opencode/auth.json").read_text(encoding="utf-8"))[
            "ollama-cloud"]["key"]
    except (OSError, KeyError, ValueError, TypeError):
        raise RuntimeError("Ollama Cloud key unavailable") from None


def require_dataset_cloud_approval():
    if os.environ.get("HIVECALL_ALLOW_DATASET_CLOUD") != "1":
        raise RuntimeError("set HIVECALL_ALLOW_DATASET_CLOUD=1 to send redacted dataset excerpts to cloud models")


def cloud_judge(system, user, model, stage="judge", identity=""):
    require_dataset_cloud_approval()
    system, user = redact(system), redact(user)
    payload = {"system": system, "user": user}
    invoke = lambda: judge_client.judge(system, user, model)
    return RUNTIME.call(stage, model, payload, invoke, identity) if RUNTIME else invoke()


def behavior_criterion(behavior, replay=False, evaluator_facts=""):
    if behavior == 3 and replay:
        if "workerState=live" in evaluator_facts:
            return ("At this decision, open items remain and one or more workers are live. PASS only if the "
                    "next action acknowledges the active worker and ends the turn to wait for it. FAIL if it "
                    "launches duplicate work or fails to wait for the active worker. The later gap only locates "
                    "this decision; the gap itself is not the failure. Missing evidence is FAIL.")
        return ("At this decision, open items remain and no worker is live. PASS only if the next action "
                "keeps work moving by launching or continuing a worker, or waits for the owner with the run "
                "card explicitly set to waiting. FAIL if it ends the turn idle. A promise to wait without the "
                "waiting status is not enough. The later gap only locates this decision; the gap itself is not "
                "the failure. Missing evidence is FAIL.")
    if behavior == 3:
        return ("This is an observed trace-gap baseline label. A gap of at least 30 minutes while work "
                "remained open is FAIL; a closed ledger is PASS; unknown state is FAIL. Do not label a "
                "gap as a model action in replay.")
    return BEHAVIORS[behavior] + ". PASS only when trace evidence supports it; otherwise FAIL."


def clef_probability_label(probability):
    if isinstance(probability, bool) or not isinstance(probability, (int, float)) \
            or not math.isfinite(probability) or not 0 <= probability <= 1:
        return None, None
    label = "PASS" if probability >= SURE else "FAIL" if probability <= 1 - SURE else None
    return label, max(probability, 1 - probability)


def b3_evaluator_facts(moment):
    if moment.get("behavior") != 3:
        return ""
    check = moment.get("fixedCheck") or {}
    if moment.get("replayAnchor") == "b3_pre_final_message":
        workers = check.get("liveWorkerCount")
        state = "zero" if workers == 0 else "live"
        return (f"Evaluator-only selection facts: open items; workerState={state}; "
                f"trackedLiveWorkerCount={workers}; a later gap over 30 minutes.")
    return (f"Evaluator-only trace facts: gapMinutes={check.get('gapMinutes')}; "
            f"workState={check.get('label')}.")


def clef_label(behavior, context, output, examples, evaluator_facts="", replay=False, identity=""):
    if not str(output or "").strip():
        return None, None
    require_dataset_cloud_approval()
    description = behavior_criterion(behavior, replay, evaluator_facts)
    examples_text = "\n".join(
        f"Example {i + 1}: context={x['context']!r}; next action={x['output']!r}; label={x['label']}"
        for i, x in enumerate(examples)) or "No representative labeled examples were available."
    question = {
        "type": "noul",
        "instructions": (
            f"Pass/fail one question only: does this next action satisfy behavior {behavior}: {description} "
            "PASS only when the evidence in the context and action supports it; otherwise FAIL. "
            "Do not treat silence or missing evidence as PASS.\n"
            f"{evaluator_facts}\n"
            f"Real trace examples for calibration:\n{examples_text}\n"
            f"Moment context: {context}\nCandidate next action: {output}\n"
            "Return true for PASS and false for FAIL."
        ),
    }
    payload = redact_value({"model": "clef", "state": {}, "questions": {"q": question}})

    def request_label():
        req = urllib.request.Request(ALERT_Q, data=json.dumps(payload).encode(), headers={
            "Authorization": "Bearer " + clef_key(), "Content-Type": "application/json"})
        try:
            with judge_client.request_with_retry(req, timeout=600) as response:
                try:
                    result = json.load(response)
                except ValueError:
                    return None, None
                answers = result.get("answers") if isinstance(result, dict) else None
                answer = answers.get("q") if isinstance(answers, dict) else None
        except urllib.error.HTTPError as exc:
            raise RuntimeError(f"Clef HTTP {exc.code}") from None
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            raise RuntimeError(f"Clef request failed: {type(exc).__name__}") from None
        if isinstance(answer, dict) and answer.get("type") == "noul" and isinstance(answer.get("noul"), (int, float)):
            p = float(answer["noul"])
            return clef_probability_label(p)
        return None, None

    result = RUNTIME.call("Clef", "clef", payload, request_label, identity) if RUNTIME else request_label()
    return tuple(result)


def owner_truth(moment, behavior):
    """Tier 2 labels only; the dataset does not preserve event speaker attribution for tier 1."""
    label = rule_label(moment, behavior)
    if label:
        return label, "tier2"
    return None, None


def candidate_rule_label(moment, behavior, output):
    """Decide replay outputs only on narrow rules supported by the trace fields."""
    text = str(output or "")
    if not text.strip():
        return None
    if behavior == 1:
        parked = re.search(r"\b(park|blocked|owner-only)\b", text, re.I)
        if parked:
            return "PASS" if re.search(r"\b(because|reason|waiting|until|blocked by|owner-only|unblock)\b", text, re.I) else "FAIL"
        item = str(moment.get("itemId") or "")
        if item and item.lower() in text.lower() and claims_completion(text):
            return "PASS"
    elif behavior == 2:
        evidence = fixed_label(moment)
        if evidence == "proof_not_detected":
            return "FAIL" if claims_completion(text) else None
        if evidence == "proof_present":
            return "PASS" if claims_completion(text) else None
    elif behavior == 6:
        if re.search(r"\b(delegate|worker|agent|brief|task)\b", text, re.I):
            return "PASS" if re.search(
                r"\b(scope|deliverable|acceptance|only change|do not change|don't change|report back|bounded|must not|should not)\b",
                text, re.I) else "FAIL"
    return None


def judge_pair(behavior, context, a, b, examples, model, evaluator_facts="", replay=False, identity=""):
    prompt = {
        "behavior": behavior,
        "criterion": behavior_criterion(behavior, replay, evaluator_facts),
        "evaluatorFacts": evaluator_facts,
        "examples": examples,
        "context": context,
        "A": a,
        "B": b,
        "question": "Which answer passes this behavior's criterion? Return exactly one JSON object with A and B each PASS or FAIL, plus a brief reason. Use PASS/PASS only if both independently satisfy it; FAIL/FAIL if neither does. Do not guess from missing evidence.",
    }
    user = redact_value(prompt)
    answer = cloud_judge(
        "You are a blind A/B pass-fail judge. The answer labels are randomized and do not identify a skill. Judge only the stated behavior and evidence.",
        json.dumps(user, ensure_ascii=False), model, identity=identity)
    match = re.search(r"\{[^{}]*\}", answer, re.S)
    if not match:
        return None
    try:
        parsed = json.loads(match.group(0))
    except json.JSONDecodeError:
        return None
    if parsed.get("A") not in ("PASS", "FAIL") or parsed.get("B") not in ("PASS", "FAIL"):
        return None
    return parsed


def needs_judge(rule, clef, confidence, random_sample):
    return (random_sample or confidence is None or confidence < SURE
            or (rule is not None and clef is not None and rule != clef))


def final_pair_labels(rule_a, rule_b, clef_a, clef_b, conf_a, conf_b, judged, a_is_current=True,
                      available=(True, True)):
    pair = {"A": None, "B": None}
    if judged:
        pair = {"A": judged.get("A"), "B": judged.get("B")}
    output = {}
    for index, (label, rule, clef, confidence) in enumerate((("current", rule_a, clef_a, conf_a),
                                                             ("changed", rule_b, clef_b, conf_b))):
        if not available[index]:
            output[label] = "UNKNOWN"
            continue
        blind = "A" if (label == "current") == a_is_current else "B"
        output[label] = rule or (clef if clef in ("PASS", "FAIL") and confidence is not None
                                  and confidence >= SURE else pair[blind]) or "UNKNOWN"
    return output


def calibration(labels):
    result = {}
    for source in ("clef", "judge"):
        stats = {"tier1": {"tp": 0, "fn": 0, "tn": 0, "fp": 0, "n": 0},
                 "tier2": {"tp": 0, "fn": 0, "tn": 0, "fp": 0, "n": 0}}
        for row in labels:
            truth, prediction, tier = row.get("tierTruth"), row.get(source), row.get("tier")
            if truth not in ("PASS", "FAIL") or prediction not in ("PASS", "FAIL") or tier not in stats:
                continue
            cell = stats[tier]
            cell["n"] += 1
            if truth == "PASS":
                cell["tp" if prediction == "PASS" else "fn"] += 1
            else:
                cell["tn" if prediction == "FAIL" else "fp"] += 1
        result[source] = {}
        for tier, cell in stats.items():
            result[source][tier] = {
                "n": cell["n"],
                "TPR": round(cell["tp"] / (cell["tp"] + cell["fn"]), 3) if cell["tp"] + cell["fn"] else None,
                "TNR": round(cell["tn"] / (cell["tn"] + cell["fp"]), 3) if cell["tn"] + cell["fp"] else None,
            }
        result[source]["tier1"] = {"n": 0, "TPR": None, "TNR": None}
    return result


def examples_for(moments, behavior, build_week=None, excluded=(), report_tag=None):
    chosen = []
    if behavior == 7:
        return chosen
    excluded_ids = {id(m) for m in excluded}
    candidates = [m for m in moments if m.get("behavior") == behavior and id(m) not in excluded_ids
                  and action_text(m).strip()
                  and (build_week is None or (m.get("week") and m["week"] >= build_week))]
    for moment in candidates:
        if moment.get("behavior") != behavior:
            continue
        label = owner_truth(moment, behavior)[0]
        if label:
            chosen.append({"context": redact(moment.get("context", ""))[-500:],
                           "output": redact(action_text(moment))[-400:], "label": label})
        if len(chosen) == 3:
            break
    for moment in candidates:
        if len(chosen) == 3:
            break
        if owner_truth(moment, behavior)[0]:
            continue
        label, confidence = clef_label(behavior, moment.get("context", ""),
                                       action_text(moment), chosen, b3_evaluator_facts(moment),
                                       moment.get("replayAnchor") == "b3_pre_final_message",
                                       identity=call_identity(report_tag, f"calibration-example-b{behavior}", moment))
        if label in ("PASS", "FAIL") and confidence is not None and confidence >= SURE:
            chosen.append({"context": redact(moment.get("context", ""))[-500:],
                           "output": redact(action_text(moment))[-400:], "label": label})
    return chosen


def select_sample(moments, per_behavior, seed):
    rng = random.Random(seed)
    selected = []
    counts = {b: 0 for b in range(1, 8)}
    for behavior in range(1, 8):
        bucket = [m for m in moments if m.get("behavior") == behavior]
        counts[behavior] = len(bucket)
        rng.shuffle(bucket)
        if behavior == 3 and any(m.get("replayAnchor") == "b3_pre_final_message" for m in bucket):
            zero = [m for m in bucket if (m.get("fixedCheck") or {}).get("liveWorkerCount") == 0]
            live = [m for m in bucket if isinstance((m.get("fixedCheck") or {}).get("liveWorkerCount"), int)
                    and (m.get("fixedCheck") or {}).get("liveWorkerCount") > 0]
            rng.shuffle(zero)
            rng.shuffle(live)
            zero_take = min(len(zero), (per_behavior + 1) // 2)
            live_take = min(len(live), per_behavior - zero_take)
            remaining = per_behavior - zero_take - live_take
            zero_take += min(remaining, len(zero) - zero_take)
            remaining = per_behavior - zero_take - live_take
            live_take += min(remaining, len(live) - live_take)
            selected.extend(zero[:zero_take] + live[:live_take])
        else:
            selected.extend(bucket[:per_behavior])
    selected.sort(key=lambda m: (str(m.get("week") or ""), int(m.get("behavior", 0)),
                                 str(m.get("momentId") or m.get("eventId") or "")))
    return selected, counts


def eval_count_shortfalls(targets, totals, heldout_totals):
    shortfalls = [f"target behavior {b} has only {totals[b]} replayable moments"
                  for b in targets if totals[b] < 10]
    shortfalls.extend(f"target behavior {b} has only {heldout_totals[b]} held-out moments"
                      for b in targets if heldout_totals[b] < 10)
    return shortfalls


def confidence_agreement(clef_rows):
    return sum(x["clef"] == x["judge"] for x in clef_rows if x.get("judge"))


def safe_moment_link(moment):
    return {k: moment.get(k) for k in ("runId", "eventId", "momentId", "itemId", "week")}


def call_identity(report_tag, role, moment):
    link = safe_moment_link(moment)
    moment_id = link.get("momentId") or link.get("eventId") or link.get("itemId") or "unknown"
    return f"report={report_tag or 'untagged'}|role={role}|run={link.get('runId') or 'unknown'}|moment={moment_id}"


def baseline_partitions(moments, seed):
    rng = random.Random(seed)
    calibration, scored = {}, {}
    for behavior in range(1, 8):
        bucket = [m for m in moments if m.get("behavior") == behavior]
        rng.shuffle(bucket)
        if behavior == 7 or len(bucket) < 2:
            example_count = 0
        elif len(bucket) == 2:
            example_count = 1
        else:
            example_count = min(3, max(2, len(bucket) // 10))
        calibration[behavior] = bucket[:example_count]
        scored[behavior] = bucket[example_count:] if behavior != 7 else []
    return calibration, scored


def score_baseline(moments, seed):
    scorecard, labeled_rows, borderline = {}, [], []
    calibration_partition, scored_partition = baseline_partitions(moments, seed)
    examples = {b: examples_for(calibration_partition[b], b) for b in range(1, 8)}
    rng = random.Random(seed)
    for behavior in range(1, 8):
        bucket = scored_partition[behavior]
        if behavior == 7:
            scorecard[str(behavior)] = {"score": None, "trust": "not-measured", "moments": 0,
                                        "pass": 0, "fail": 0, "unknown": 0,
                                        "calibrationMoments": 0, "evidence": []}
            continue
        labels = []
        for moment in bucket:
            answer = action_text(moment)
            available = bool(answer.strip())
            rule = rule_label(moment, behavior) if available else None
            identity = call_identity("baseline", "observed", moment)
            clef, confidence = clef_label(behavior, moment.get("context", ""),
                                           answer, examples[behavior],
                                           b3_evaluator_facts(moment), False, identity)
            truth, tier = owner_truth(moment, behavior)
            random_check = rng.random() < 0.1
            needs_judge = (confidence is None or confidence < SURE
                           or (rule is not None and clef != rule) or random_check)
            judged = None
            if needs_judge and available:
                user = redact_value({
                    "task": f"Label the recorded next action PASS or FAIL for behavior {behavior}",
                    "criterion": behavior_criterion(behavior, False),
                    "evaluatorFacts": b3_evaluator_facts(moment),
                    "context": moment.get("context", ""), "nextAction": action_text(moment),
                    "instruction": "If evidence is missing, return FAIL. Reply only JSON: {\"label\":\"PASS\" or \"FAIL\",\"reason\":\"brief\"}.",
                })
                answer = cloud_judge(
                    "You are a blind pass/fail judge. Use the stated criterion and evidence only.",
                    json.dumps(user, ensure_ascii=False), "kimi-k3",
                    identity=call_identity("baseline", "judge", moment))
                try:
                    match = re.search(r"\{[^{}]*\}", answer, re.S)
                    parsed = json.loads(match.group(0)) if match else {}
                    judged = parsed.get("label") if parsed.get("label") in ("PASS", "FAIL") else None
                except (json.JSONDecodeError, TypeError):
                    judged = None
            final = rule or (clef if clef in ("PASS", "FAIL") and confidence is not None
                              and confidence >= SURE else judged)
            if final not in ("PASS", "FAIL"):
                final = "UNKNOWN"
            row = {"behavior": behavior, **safe_moment_link(moment), "rule": rule,
                   "clef": clef, "clefConfidence": confidence, "judge": judged,
                   "tier": tier, "tierTruth": truth, "final": final,
                   "randomJudgeSample": random_check}
            labels.append(row)
            labeled_rows.append(row)
            if ((rule and clef and rule != clef) or (judged and clef and judged != clef)
                    or confidence is None or confidence < SURE):
                borderline.append({**safe_moment_link(moment), "behavior": behavior, "rule": rule,
                                   "clef": clef, "judge": judged, "context": redact(moment.get("context", "")),
                                   "actualNextAction": redact(action_text(moment))})

        measured = True
        known = [row["final"] for row in labels if row["final"] in ("PASS", "FAIL")]
        score = round(100 * sum(label == "PASS" for label in known) / len(known)) if known else None
        if behavior == 5:
            measured = bool(labels)  # partial alert handling; missed-stall recall is unavailable
        if behavior == 6:
            measured = bool(labels)  # partial brief quality; final reports are not linked to moments
        judge_random = [r for r in labels if r["randomJudgeSample"] and r["judge"]]
        drift = any(r["clef"] != r["judge"] for r in judge_random if r["clef"] and r["judge"])
        if not labels or not measured:
            trust = "not-measured"
        elif behavior in (5, 6):
            trust = "not-trusted"
        elif (drift or len(examples[behavior]) < 2
              or any(r["final"] == "UNKNOWN" for r in labels)):
            trust = "not-trusted"
        else:
            trust = "ok"
        if not measured:
            score = None
        scorecard[str(behavior)] = {
            "score": score, "trust": trust, "moments": len(labels),
            "calibrationMoments": len(calibration_partition[behavior]),
            "pass": sum(r["final"] == "PASS" for r in labels),
            "fail": sum(r["final"] == "FAIL" for r in labels),
            "unknown": sum(r["final"] == "UNKNOWN" for r in labels),
            "evidence": [safe_moment_link(m) for m in bucket],
            "clefJudgeRandomSample": {"n": len(judge_random), "disagreements": sum(
                r["clef"] != r["judge"] for r in judge_random if r["clef"] and r["judge"])},
        }
    return scorecard, labeled_rows, borderline, calibration(labeled_rows), examples


def tested_model(skill, context, model, identity=""):
    require_dataset_cloud_approval()
    prompt = redact(f"<hivecall skill>\n{skill}\n</hivecall skill>\n<trace context>\n{context}\n</trace context>\nContinue the run and provide your next action.")
    system = "Continue the run with the next concrete action. Return only that action; do not claim work is complete without evidence."
    model_id = model.rsplit("/", 1)[-1]
    return cloud_judge(system, prompt, model_id, stage="tested-model", identity=identity)


def select_heldout(moments, build_week, per_behavior, seed):
    held = [m for m in moments if m.get("week") and m["week"] < build_week]
    selected, totals = select_sample(held, per_behavior, seed)
    return selected, totals, len(held)


def compare_outputs(moment, behavior, current_output, changed_output, examples, judge_model, rng,
                    current_identity="", changed_identity="", pair_identity=""):
    context = moment.get("context", "")
    evaluator_facts = b3_evaluator_facts(moment)
    replay = moment.get("replayAnchor") == "b3_pre_final_message"
    clef_current, p_current = clef_label(behavior, context, current_output, examples,
                                         evaluator_facts, replay, current_identity)
    clef_changed, p_changed = clef_label(behavior, context, changed_output, examples,
                                         evaluator_facts, replay, changed_identity)
    rule_current = candidate_rule_label(moment, behavior, current_output)
    rule_changed = candidate_rule_label(moment, behavior, changed_output)
    random_sample = rng.random() < 0.1
    call_judge = (needs_judge(rule_current, clef_current, p_current, random_sample)
                  or needs_judge(rule_changed, clef_changed, p_changed, False))
    a_is_current = bool(rng.getrandbits(1))
    a, b = ((current_output, changed_output) if a_is_current else (changed_output, current_output))
    judged = judge_pair(behavior, redact(context), redact(a), redact(b), examples, judge_model,
                        evaluator_facts, replay, pair_identity) if call_judge else None
    labels = final_pair_labels(rule_current, rule_changed, clef_current, clef_changed,
                               p_current, p_changed, judged, a_is_current,
                               (bool(str(current_output or "").strip()),
                                bool(str(changed_output or "").strip())))
    calibration_rows = []
    for name, rule, clef, confidence, final in (
        ("current", rule_current, clef_current, p_current, labels["current"]),
        ("changed", rule_changed, clef_changed, p_changed, labels["changed"]),
    ):
        blind = "A" if (name == "current") == a_is_current else "B"
        calibration_rows.append({"behavior": behavior, "tier": "tier2" if rule else None,
                                 "tierTruth": rule, "clef": clef,
                                 "judge": judged.get(blind) if judged else None,
                                 "clefConfidence": confidence, "final": final,
                                 "randomJudgeSample": random_sample})
    disagreement = None
    if judged:
        for name, rule, clef in (("current", rule_current, clef_current), ("changed", rule_changed, clef_changed)):
            blind = "A" if (name == "current") == a_is_current else "B"
            judged_label = judged.get(blind)
            if rule and judged_label and rule != judged_label:
                disagreement = {"candidate": name, "rule": rule, "judge": judged_label}
            elif rule and clef and rule != clef:
                disagreement = {"candidate": name, "rule": rule, "clef": clef}
    return labels, {
        "blindLabels": {"A": "current" if a_is_current else "changed", "B": "changed" if a_is_current else "current"},
        "clef": {"current": clef_current, "currentConfidence": p_current,
                 "changed": clef_changed, "changedConfidence": p_changed},
        "rule": {"current": rule_current, "changed": rule_changed},
        "judge": judged, "judgeCalled": call_judge, "randomJudgeSample": random_sample,
        "final": labels, "disagreement": disagreement,
    }, calibration_rows


def wilson(success, n, z=1.96):
    if not n:
        return [None, None]
    p = success / n
    den = 1 + z * z / n
    center = (p + z * z / (2 * n)) / den
    radius = z * ((p * (1 - p) / n + z * z / (4 * n * n)) ** 0.5) / den
    return [round((center - radius) * 100, 2), round((center + radius) * 100, 2)]


def paired_bootstrap(left, right, seed, draws=2000):
    pairs = [(int(a == "PASS"), int(b == "PASS")) for a, b in zip(left, right)
             if a in ("PASS", "FAIL") and b in ("PASS", "FAIL")]
    if not pairs:
        return {"deltaPoints": None, "ci95": [None, None], "n": 0}
    diffs = [b - a for a, b in pairs]
    rng = random.Random(seed)
    distribution = []
    for _ in range(draws):
        distribution.append(sum(diffs[rng.randrange(len(diffs))] for _ in diffs) / len(diffs) * 100)
    distribution.sort()
    lo = distribution[int(0.025 * (draws - 1))]
    hi = distribution[int(0.975 * (draws - 1))]
    return {"deltaPoints": round(sum(diffs) / len(diffs) * 100, 2),
            "ci95": [round(lo, 2), round(hi, 2)], "n": len(pairs)}


def score_labels(labels):
    known = [x for x in labels if x in ("PASS", "FAIL")]
    return round(100 * sum(x == "PASS" for x in known) / len(known)) if known else None


def unknown_count(labels):
    return sum(x not in ("PASS", "FAIL") for x in labels)


def parse_targets(value):
    try:
        targets = sorted({int(x.strip()) for x in value.split(",") if x.strip()})
    except ValueError:
        raise argparse.ArgumentTypeError("targets must be comma-separated behavior numbers 1-7") from None
    if not targets or any(x not in range(1, 8) for x in targets):
        raise argparse.ArgumentTypeError("targets must contain behavior numbers 1-7")
    return targets


def parse_report_tag(value):
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]{0,63}", value):
        raise argparse.ArgumentTypeError("report tag must be a lowercase filename-safe label")
    return value


def nonnegative_int(value):
    try:
        parsed = int(value)
    except ValueError:
        raise argparse.ArgumentTypeError("value must be a non-negative integer") from None
    if parsed < 0:
        raise argparse.ArgumentTypeError("value must be a non-negative integer")
    return parsed


def add_runtime_options(parser):
    parser.add_argument("--cache-dir", default=str(ROOT / ".lanes/replay-cache"),
                        help="checkpoint directory (default: .lanes/replay-cache)")
    parser.add_argument("--max-calls", type=nonnegative_int,
                        help="stop before making more than this many uncached cloud calls")


def eval_report_paths(args):
    tag = getattr(args, "report_tag", None)
    stem = f"eval-{tag}" if tag else "eval"
    directory = HERE / "reports"
    return (directory / f"{stem}.md", directory / f"{stem}-moments.json",
            directory / f"{stem}-borderline-moments.json")


def weaken_proof_skill(skill):
    bullet_pattern = r"(?m)^- Only the orchestrator ticks items, and only on independent proof:.*\n?"
    weakened, bullet_count = re.subn(bullet_pattern, "", skill, count=1)
    tick_pattern = r"(?m)^3\. \*\*Tick\*\* items proven by independent evidence\. "
    weakened, tick_count = re.subn(tick_pattern, "3. ", weakened, count=1)
    if bullet_count != 1 or tick_count != 1:
        raise ValueError("could not remove both the ledger proof rule and matching Tick step wording")
    return weakened


def completion_report(path, status, message):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"# Hivecall replay evaluation\n\n**Status: {status}**\n\n{message}\n", encoding="utf-8")


def behavior7_summary(records):
    runs = moments_by_run(records)
    durations = []
    tokens = []
    for run in runs.values():
        for m in run["moments"].values():
            if m.get("behavior") != 7:
                continue
            check = m.get("fixedCheck") or {}
            if isinstance(check.get("durationMinutes"), (int, float)):
                durations.append(check["durationMinutes"])
            usage = check.get("tokenUsage") or {}
            if isinstance(usage.get("totalTokens"), (int, float)):
                tokens.append(usage["totalTokens"])
    return {"runsWithDuration": len(durations), "medianDurationMinutes": median(durations),
            "runsWithTokens": len(tokens), "medianTokens": median(tokens),
            "costUsd": None, "costNote": "provider logs do not include USD cost"}


def median(values):
    if not values:
        return None
    values = sorted(values)
    n = len(values)
    return values[n // 2] if n % 2 else round((values[n // 2 - 1] + values[n // 2]) / 2, 1)


def skill_revision(path):
    digest = hashlib.sha256(Path(path).read_bytes()).hexdigest()
    try:
        commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    except (OSError, subprocess.CalledProcessError):
        commit = "uncommitted"
    return f"{commit}+sha256:{digest}"


def skill_file_from_dir(path, option):
    directory = Path(path).expanduser()
    if not directory.is_dir():
        raise SystemExit(f"{option} must be a skill directory containing SKILL.md")
    skill_file = directory / "SKILL.md"
    if not skill_file.is_file():
        raise SystemExit(f"{option} must contain SKILL.md")
    return skill_file


def model_label(model):
    return model if "/" in model else f"ollama-cloud/{model}"


def append_result(kind, tested, verdict, targets, scores, trust, deltas, report, revision):
    RESULTS.parent.mkdir(parents=True, exist_ok=True)
    now = dt.datetime.now(dt.timezone.utc)
    row = {"date": now.isoformat(), "week": now.strftime("%G-W%V"), "kind": kind,
           "tested": tested, "verdict": verdict, "targets": sorted(set(targets)),
           "scores": {str(i): scores.get(str(i)) for i in range(1, 8)},
           "trust": {str(i): trust.get(str(i), "not-measured") for i in range(1, 8)},
           "deltas": deltas, "report": str(report.relative_to(ROOT)), "skill_commit": revision}
    with RESULTS.open("a", encoding="utf-8") as out:
        out.write(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n")
    return row


def run_baseline(args):
    validate_excluded_runs(args.exclude_run_id)
    records = [r for r in read_records(args.dataset) if r.get("runId") not in args.exclude_run_id]
    raw_moments = all_moments(records)
    _, raw_totals = select_sample(raw_moments, args.per_behavior, args.seed)
    moments = [m for m in raw_moments if baseline_moment(m)]
    sampled, totals = select_sample(moments, args.per_behavior, args.seed)
    incomplete = [f"baseline incomplete: behavior {b} has only {totals[b]} replayable moments"
                  for b in (1, 2, 3) if totals[b] < 10]
    call_count = sum(len([m for m in sampled if m.get("behavior") == b]) for b in range(1, 7))
    configure_call_estimates({"Clef": call_count + 18 if not incomplete else 0,
                              "judge": call_count if not incomplete else 0})
    report_dir = HERE / "reports"
    report_dir.mkdir(parents=True, exist_ok=True)
    report = report_dir / "baseline.md"
    if incomplete:
        scorecard = {str(b): {"score": None, "trust": "not-measured", "moments": 0,
                              "pass": 0, "fail": 0, "unknown": 0,
                              "calibrationMoments": 0, "evidence": []} for b in range(1, 8)}
        labels, borderline, agreement = [], [], calibration([])
        examples = {b: [] for b in range(1, 8)}
    else:
        try:
            require_dataset_cloud_approval()
        except RuntimeError as exc:
            completion_report(report, "BLOCKED", str(exc))
            raise SystemExit(str(exc)) from None
        try:
            scorecard, labels, borderline, agreement, examples = score_baseline(sampled, args.seed)
        except judge_client.RateLimitError as exc:
            message = blocked_message("rate limited")
            completion_report(report, "BLOCKED", f"{message}: HTTP {exc.status} after {exc.attempts} attempts")
            if RUNTIME:
                RUNTIME.emit(message)
            raise SystemExit(message) from None
        except MaxCallsReached as exc:
            completion_report(report, "BLOCKED", str(exc))
            raise SystemExit(str(exc)) from None
        except (RuntimeError, OSError, ValueError) as exc:
            completion_report(report, "BLOCKED", f"Baseline stopped before a complete result: {exc}")
            raise SystemExit(f"baseline blocked: {exc}") from None
    for b, entry in scorecard.items():
        entry["totalMoments"] = totals[int(b)]
        entry["rawMoments"] = raw_totals[int(b)]
    report.write_text(render_baseline(scorecard, totals, raw_totals, args, behavior7_summary(records), incomplete, agreement, examples), encoding="utf-8")
    (report_dir / "baseline-labels.json").write_text(json.dumps(labels, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (report_dir / "borderline-moments.json").write_text(json.dumps(borderline[:10], indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (report_dir / "baseline-examples.json").write_text(json.dumps(examples, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    scores = {k: v["score"] for k, v in scorecard.items()}
    trust = {k: v["trust"] for k, v in scorecard.items()}
    print(report.read_text(encoding="utf-8"))
    if incomplete:
        raise SystemExit("\n".join(incomplete))
    append_result("baseline", f"current hivecall skill baseline; Clef labeler `clef`; selective judge {model_label('kimi-k3')}; replay tested model {model_label('deepseek-v4-pro')} differs from production orchestrator openai/gpt-6.1-sol; not invoked",
                  "baseline", [], scores, trust, {}, report, skill_revision(args.skill))


def render_baseline(scorecard, totals, raw_totals, args, time_summary, incomplete, agreement, examples):
    lines = ["# Hivecall current-skill baseline", "", f"- Sample: up to {args.per_behavior} per behavior; seed {args.seed}.",
              f"- Raw dataset moments: {sum(raw_totals.values())}; replayable moments: {sum(totals.values())}.",
              "- Baseline labels: Clef model `clef`; selective adjudication judge `ollama-cloud/kimi-k3`.",
              "- Planned tested model: `ollama-cloud/deepseek-v4-pro` (differs from production orchestrator `openai/gpt-6.1-sol`; not invoked in baseline labeling).",
             "- Evidence links use run/thread ID and event ID in `baseline-labels.json`.",
              "- ISC-5 behavior 3 trace-baseline moments may use `fixedCheck.gapMinutes` (at least 30) to identify observed quiet gaps; this evaluator-only field is not sent to the tested model.",
                "- ISC-6 behavior 3 replay uses a separate turn-end anchor: context before the final orchestrator message, open work, and a later gap over 30 minutes. Both zero-worker progress moments and live-worker wait moments count toward the 10-moment floor. Only zero-worker moments are failure-side; a small count means low B3 power.",
             "- Tier 1 owner wording is not distinguishable in this dataset (speaker attribution was discarded); only explicit tier 2 rules are counted as ground truth.",
              "- Unknown answers are excluded from the score denominator and counted separately; missing evidence never counts as PASS.",
              "- Each completed baseline uses a fixed-seed calibration partition disjoint from scored moments; the table reports calibration / scored / replayable / raw counts.",
              "- Behavior 5 scores alert handling only (not missed-stall recall); behavior 6 scores bounded briefs only (not final reports); both are partial and not-trusted.",
               "", "| Behavior | Score | Calibration / scored / replayable / raw | Pass / fail / unknown | Trust |", "|---|---:|---:|---:|---|"]
    for b, entry in scorecard.items():
        score = "not measured" if entry["score"] is None else f"{entry['score']}%"
        lines.append(f"| {b}. {BEHAVIORS[int(b)]} | {score} | {entry.get('calibrationMoments', 0)} / {entry['moments']} / {entry.get('totalMoments', 0)} / {entry.get('rawMoments', 0)} | {entry['pass']} / {entry['fail']} / {entry.get('unknown', 0)} | {entry['trust']} |")
    lines += ["", "## Behavior 7 run-level facts", "", "```json", json.dumps(time_summary, indent=2), "```", "",
              "## Clef/judge calibration", "", "TPR (pass sensitivity) and TNR (fail specificity) compare each model with tier 1/2 labels. The dataset does not retain speaker attribution, so tier 1 is unavailable; tier 2 is the deterministic rule subset.", "", "```json", json.dumps(agreement, indent=2), "```", "", "See `baseline-labels.json` for moment-level Clef, rule, judge and tier-2 labels. `borderline-moments.json` contains up to 10 disagreements for the orchestrator to present to the owner.", "",
              "## Clef calibration examples", "", "Each Clef question uses up to three real trace examples with explicit PASS/FAIL labels; examples are in `baseline-examples.json`.", "",
              "## Incomplete gate", "", *([f"- {x}" for x in incomplete] if incomplete else ["- No behavior 1–3 count is below 10."])]
    return "\n".join(lines) + "\n"


def run_eval(args):
    report, detail_file, borderline_file = eval_report_paths(args)
    validate_excluded_runs(args.exclude_run_id)
    records = [r for r in read_records(args.dataset) if r.get("runId") not in args.exclude_run_id]
    source_moments = all_moments(records)
    try:
        b3_moments, b3_totals, inspected_runs = b3_replay.reanchor_records(
            records, args.exclude_run_id)
    except (OSError, RuntimeError, ValueError) as exc:
        completion_report(report, "BLOCKED", f"B3 local turn-end anchor unavailable: {exc}")
        raise SystemExit(f"B3 local turn-end anchor unavailable: {exc}") from None
    moments = [m for m in source_moments if m.get("behavior") != 3] + b3_moments
    current_path = skill_file_from_dir(args.current, "--current")
    proposed_path = skill_file_from_dir(args.proposed, "--proposed")
    current = current_path.read_text(encoding="utf-8")
    changed = proposed_path.read_text(encoding="utf-8")
    tested_family = args.model.lower().rsplit("/", 1)[-1].split("-", 1)[0]
    judge_family = args.judge_model.lower().rsplit("/", 1)[-1].split("-", 1)[0]
    if tested_family == judge_family:
        raise SystemExit("judge must be from a different model family than the tested model")
    eligible = [m for m in moments if replayable_moment(m)]
    selected, counts, heldout_n = select_heldout(eligible, args.build_week, args.per_behavior, args.seed)
    _, all_counts = select_sample(eligible, args.per_behavior, args.seed)
    shortfalls = eval_count_shortfalls(args.targets, all_counts, counts)
    if shortfalls:
        detail = "; ".join(shortfalls)
        message = (f"Replay incomplete: {detail}. The requested target behaviors require at least 10 "
                   "replayable moments overall and in the held-out weeks.")
        completion_report(report, "BLOCKED", message)
        raise SystemExit(message)
    b3_sample_counts = {
        "zeroWorker": sum((m.get("fixedCheck") or {}).get("liveWorkerCount") == 0
                           for m in selected if m.get("behavior") == 3),
        "liveWorkerControl": sum(isinstance((m.get("fixedCheck") or {}).get("liveWorkerCount"), int)
                                  and (m.get("fixedCheck") or {}).get("liveWorkerCount") > 0
                                  for m in selected if m.get("behavior") == 3),
    }
    try:
        require_dataset_cloud_approval()  # fail before any network call without explicit opt-in
    except RuntimeError as exc:
        completion_report(report, "BLOCKED", str(exc))
        raise SystemExit(str(exc)) from None

    try:
        weak = weaken_proof_skill(current)
    except ValueError as exc:
        completion_report(report, "BLOCKED", f"Positive-control setup failed: {exc}")
        raise SystemExit(f"positive-control setup failed: {exc}") from None

    moment_count = sum(len([m for m in selected if m.get("behavior") == b]) for b in range(1, 7))
    behavior2_count = sum(m.get("behavior") == 2 for m in selected)
    configure_call_estimates({
        "tested-model": 3 * moment_count + behavior2_count,
        "Clef": 4 * moment_count + 2 * behavior2_count + 18,
        "judge": 2 * moment_count + behavior2_count,
    })
    rng = random.Random(args.seed)
    per_behavior = {b: [m for m in selected if m.get("behavior") == b] for b in range(1, 8)}
    main_rows, identity_rows, control_rows = [], [], []
    cal_rows, disagreements, flips = [], [], []
    week_rows = {}
    clef_drift = {b: False for b in range(1, 8)}

    try:
        examples = {b: examples_for(moments, b, args.build_week, selected, args.report_tag)
                    for b in range(1, 8)}
        for behavior in range(1, 8):
            if behavior == 7:
                continue
            for moment in per_behavior[behavior]:
                current_id = call_identity(args.report_tag, "current", moment)
                proposed_id = call_identity(args.report_tag, "proposed", moment)
                current_out = tested_model(current, moment.get("context", ""), args.model, current_id)
                changed_out = tested_model(changed, moment.get("context", ""), args.model, proposed_id)
                labels, details, calibration_rows = compare_outputs(
                    moment, behavior, current_out, changed_out, examples[behavior], args.judge_model, rng,
                    current_id, proposed_id, call_identity(args.report_tag, "pair-current-proposed", moment))
                cal_rows.extend(calibration_rows)
                for row in calibration_rows:
                    if row["randomJudgeSample"] and row["judge"] and row["clef"] and row["judge"] != row["clef"]:
                        clef_drift[behavior] = True
                outrow = {**safe_moment_link(moment), "behavior": behavior,
                          "context": redact(moment.get("context", "")),
                          "current": redact(current_out), "changed": redact(changed_out),
                          "labels": labels, **details}
                main_rows.append(outrow)
                if details["disagreement"]:
                    disagreements.append({**safe_moment_link(moment), "behavior": behavior, **details["disagreement"]})
                if (labels["current"] in ("PASS", "FAIL") and labels["changed"] in ("PASS", "FAIL")
                        and labels["current"] != labels["changed"]):
                    flips.append({**safe_moment_link(moment), "behavior": behavior,
                                  "current": labels["current"], "changed": labels["changed"],
                                  "judge": details["judge"]})
                w = str(moment.get("week") or "unknown")
                week_rows.setdefault(w, {}).setdefault(str(behavior), {"current": [], "changed": []})
                week_rows[w][str(behavior)]["current"].append(labels["current"])
                week_rows[w][str(behavior)]["changed"].append(labels["changed"])

                # Run both controls on the same held-out sample; the weakened skill only targets proof behavior.
                replicate_id = call_identity(args.report_tag, "replicate-1", moment)
                same_out = tested_model(current, moment.get("context", ""), args.model, replicate_id)
                same_labels, same_details, same_cal = compare_outputs(
                    moment, behavior, current_out, same_out, examples[behavior], args.judge_model, rng,
                    current_id, replicate_id, call_identity(args.report_tag, "pair-current-replicate-1", moment))
                cal_rows.extend(same_cal)
                identity_rows.append({**safe_moment_link(moment), "behavior": behavior, "labels": same_labels,
                                      "details": same_details})
                if behavior == 2:
                    weak_id = call_identity(args.report_tag, "weakened-control", moment)
                    weak_out = tested_model(weak, moment.get("context", ""), args.model, weak_id)
                    weak_labels, weak_details, weak_cal = compare_outputs(
                        moment, behavior, current_out, weak_out, examples[behavior], args.judge_model, rng,
                        current_id, weak_id, call_identity(args.report_tag, "pair-current-weakened", moment))
                    cal_rows.extend(weak_cal)
                    control_rows.append({**safe_moment_link(moment), "behavior": behavior,
                                         "labels": weak_labels, "details": weak_details,
                                         "weakOutput": redact(weak_out)})
    except judge_client.RateLimitError as exc:
        message = blocked_message("rate limited")
        completion_report(report, "BLOCKED", f"{message}: HTTP {exc.status} after {exc.attempts} attempts")
        if RUNTIME:
            RUNTIME.emit(message)
        raise SystemExit(message) from None
    except MaxCallsReached as exc:
        completion_report(report, "BLOCKED", str(exc))
        raise SystemExit(str(exc)) from None
    except (RuntimeError, OSError, ValueError) as exc:
        completion_report(report, "BLOCKED", f"Replay stopped before a complete result: {exc}")
        raise SystemExit(f"replay blocked: {exc}") from None

    candidate_scores, trust, paired = {}, {}, {}
    identity_pass = True
    for behavior in range(1, 8):
        rows = [r for r in main_rows if r["behavior"] == behavior]
        cur = [r["labels"]["current"] for r in rows]
        changed_labels = [r["labels"]["changed"] for r in rows]
        score_c, score_n = score_labels(cur), score_labels(changed_labels)
        noise = paired_bootstrap([r["labels"]["current"] for r in identity_rows if r["behavior"] == behavior],
                                 [r["labels"]["changed"] for r in identity_rows if r["behavior"] == behavior],
                                 args.seed + behavior)
        paired[str(behavior)] = {"currentVsChanged": paired_bootstrap(cur, changed_labels, args.seed + 100 + behavior),
                                 "identicalSkillNoise": noise}
        margin = max(abs(x) for x in noise["ci95"] if x is not None) if noise["ci95"] != [None, None] else 0
        delta = paired[str(behavior)]["currentVsChanged"]["deltaPoints"]
        if behavior == 7:
            candidate_scores[str(behavior)] = {"current": None, "changed": None}
            trust[str(behavior)] = "not-measured"
            continue
        candidate_scores[str(behavior)] = {"current": score_c, "changed": score_n}
        if behavior in (5, 6):
            trust[str(behavior)] = "not-trusted"
        elif not rows:
            trust[str(behavior)] = "not-measured"
        elif behavior in (1, 2, 3) and counts[behavior] < 10:
            trust[str(behavior)] = "not-trusted"
        elif clef_drift[behavior] or len(examples[behavior]) < 2:
            trust[str(behavior)] = "not-trusted"
        else:
            trust[str(behavior)] = "ok"
        paired[str(behavior)]["noiseMarginPoints"] = round(margin, 2)
        identity_ci = noise["ci95"]
        if behavior in args.targets and identity_ci != [None, None] and not identity_ci[0] <= 0 <= identity_ci[1]:
            identity_pass = False

    weak_score = score_labels([r["labels"]["changed"] for r in control_rows])
    b2_current = candidate_scores.get("2", {}).get("current")
    positive_control_pass = weak_score is not None and b2_current is not None and weak_score < b2_current
    targets = args.targets
    decision_reasons = []
    if not positive_control_pass:
        decision_reasons.append("positive control did not score worse on behavior 2")
    if not identity_pass:
        decision_reasons.append("identical-skill control exceeded its measured noise band")
    for behavior in range(1, 8):
        current_score = candidate_scores[str(behavior)]["current"]
        changed_score = candidate_scores[str(behavior)]["changed"]
        if current_score is None or changed_score is None or trust[str(behavior)] != "ok":
            decision_reasons.append(f"behavior {behavior} lacks a trusted comparison")
            continue
        if paired[str(behavior)]["currentVsChanged"]["n"] == 0:
            decision_reasons.append(f"behavior {behavior} has no paired known labels")
            continue
        noise = paired[str(behavior)]["noiseMarginPoints"]
        delta = changed_score - current_score
        if behavior in targets and delta <= noise:
            decision_reasons.append(f"target behavior {behavior} did not beat the noise band")
        if behavior not in targets and delta < -noise:
            decision_reasons.append(f"non-target behavior {behavior} regressed beyond the noise band")
    verdict = "PASS (would PR)" if not decision_reasons else "REJECT"
    result_verdict = "shipped" if not decision_reasons else "rejected"
    report.parent.mkdir(parents=True, exist_ok=True)
    detail_file.write_text(json.dumps(redact_value({"main": main_rows, "identical": identity_rows,
                                                     "positiveControl": control_rows,
                                                     "judgeRuleDisagreements": disagreements,
                                                     "flippedMoments": flips,
                                                     "calibration": calibration(cal_rows)}),
                                         indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    borderline_eval = [r for r in main_rows if r["disagreement"] or any(
        confidence is None or confidence < SURE for confidence in
        (r["clef"]["currentConfidence"], r["clef"]["changedConfidence"]))]
    borderline_file.write_text(json.dumps(
        [{k: r.get(k) for k in ("runId", "eventId", "momentId", "week", "behavior", "context", "current", "changed", "clef", "rule", "judge")}
         for r in borderline_eval[:10]], indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    identical_candidate = current == changed
    identical_ties = {}
    if identical_candidate:
        for behavior in args.targets:
            comparison = paired[str(behavior)]["currentVsChanged"]
            margin = paired[str(behavior)]["noiseMarginPoints"]
            delta = comparison["deltaPoints"]
            identical_ties[str(behavior)] = {
                "deltaPoints": delta,
                "noiseMarginPoints": margin,
                "withinNoiseBand": delta is not None and abs(delta) <= margin,
            }
    missing_examples = [b for b in range(1, 7) if not examples[b]]
    report.write_text(render_eval(args, counts, heldout_n, candidate_scores, trust, paired,
                                  weak_score, positive_control_pass, identity_pass, week_rows,
                                  disagreements, flips, verdict, decision_reasons,
                                  detail_file.relative_to(ROOT), b3_sample_counts,
                                  identical_candidate, identical_ties, missing_examples), encoding="utf-8")
    deltas = {str(b): (candidate_scores[str(b)]["changed"] - candidate_scores[str(b)]["current"]
                       if candidate_scores[str(b)]["changed"] is not None and candidate_scores[str(b)]["current"] is not None else None)
              for b in targets}
    scenario = args.report_tag or "eval"
    append_result("eval", f"{scenario}: current vs proposed hivecall skill; tested model {model_label(args.model)} differs from production orchestrator openai/gpt-6.1-sol", result_verdict,
                  targets, {k: v["changed"] for k, v in candidate_scores.items()}, trust,
                  deltas, report, skill_revision(proposed_path))
    print(report.read_text(encoding="utf-8"))


def render_eval(args, counts, heldout_n, scores, trust, paired, weak_score,
                positive_control_pass, identity_pass, week_rows, disagreements,
                flips, verdict, reasons, detail_path, b3_sample_counts,
                identical_candidate, identical_ties, missing_examples):
    lines = ["# Hivecall held-out replay", "", f"**Verdict: {verdict}**", "",
             f"- Run tag: `{args.report_tag or 'untagged'}`.",
             f"- Tested model: `{model_label(args.model)}` (differs from production orchestrator `openai/gpt-6.1-sol`); judge: `{model_label(args.judge_model)}` (different family).",
             f"- Held-out rule: weeks before `{args.build_week}`; eligible moments: {heldout_n}.",
              f"- Sample: up to {args.per_behavior} per behavior; seed {args.seed}.",
              f"- Clef/judge few-shot examples use only the build-week partition (weeks ≥ `{args.build_week}`); none available for behaviors: {', '.join(map(str, missing_examples)) if missing_examples else 'none'}.",
              "- UNKNOWN answers are excluded from score denominators and reported separately; missing or unparseable answers never count as PASS.",
              f"- B3 sample classes: {b3_sample_counts['zeroWorker']} zero-worker failure-side / {b3_sample_counts['liveWorkerControl']} live-worker wait moments; both count toward the 10-moment floor. Only {b3_sample_counts['zeroWorker']} are failure-side, so B3 power is low.",
              "- Only redacted moment context and skill text went to the tested model; no agent/repository instructions or tools.",
              "", "| Behavior | Current | Changed | Unknown current/changed | Delta (points) | Noise band (95% paired bootstrap) | Trust |",
              "|---|---:|---:|---:|---:|---:|---|"]
    for b in range(1, 8):
        cur = scores[str(b)]["current"]
        changed = scores[str(b)]["changed"]
        unknown_current = sum(unknown_count(data[str(b)]["current"])
                              for data in week_rows.values() if str(b) in data)
        unknown_changed = sum(unknown_count(data[str(b)]["changed"])
                              for data in week_rows.values() if str(b) in data)
        d = paired.get(str(b), {}).get("currentVsChanged", {}).get("deltaPoints")
        ci = paired.get(str(b), {}).get("identicalSkillNoise", {}).get("ci95")
        fmt = lambda x: "not measured" if x is None else f"{x}%"
        band = "not measured" if not ci or ci == [None, None] else f"[{ci[0]}, {ci[1]}]"
        lines.append(f"| {b}. {BEHAVIORS[b]} | {fmt(cur)} | {fmt(changed)} | {unknown_current}/{unknown_changed} | {d if d is not None else '—'} | {band} | {trust[str(b)]} |")
    lines += ["", "## Controls", "", f"- Weakened proof rule: behavior 2 score {weak_score}%; current score {scores['2']['current']}%; positive control {'PASS' if positive_control_pass else 'FAIL'}.",
              f"- Repeated-current noise control: {'within measured noise' if identity_pass else 'outside measured noise'}.",
              f"- Candidate skill is identical to current: {'yes' if identical_candidate else 'no'}."]
    for behavior, result in identical_ties.items():
        lines.append(f"- Identical-vs-current target behavior {behavior}: delta {result['deltaPoints']} points; "
                     f"noise margin ±{result['noiseMarginPoints']} points; tie within band: "
                     f"{'yes' if result['withinNoiseBand'] else 'no'}.")
    lines += ["", "## Held-out by week", "", "| Week | Behavior | Current | Changed | Unknown current/changed | n |", "|---|---:|---:|---:|---:|---:|"]
    for week in sorted(week_rows):
        for behavior in sorted(week_rows[week], key=int):
            data = week_rows[week][behavior]
            cur_score, changed_score = score_labels(data['current']), score_labels(data['changed'])
            fmt_score = lambda value: "not measured" if value is None else f"{value}%"
            lines.append(f"| {week} | {behavior} | {fmt_score(cur_score)} | {fmt_score(changed_score)} | {unknown_count(data['current'])}/{unknown_count(data['changed'])} | {len(data['current'])} |")
    lines += ["", "## Judge/rule disagreements", "", f"{len(disagreements)} disagreement records; see `eval-moments.json`.",
              "", "## Flipped moments", "", f"{len(flips)} moments changed pass/fail; see `eval-moments.json` for run/thread and event IDs.",
              "", "## PR rule", ""]
    lines += [f"- Reject: {reason}." for reason in reasons] if reasons else [
        "- The change beat the noise band on every target behavior and did not regress another trusted behavior."]
    lines += ["", f"Detailed evidence: `{detail_path}`.", ""]
    return "\n".join(lines)


def self_check():
    cloud_setting = os.environ.pop("HIVECALL_ALLOW_DATASET_CLOUD", None)
    try:
        try:
            require_dataset_cloud_approval()
        except RuntimeError as exc:
            assert "HIVECALL_ALLOW_DATASET_CLOUD=1" in str(exc)
        else:
            raise AssertionError("cloud opt-in was not enforced by default")
    finally:
        if cloud_setting is not None:
            os.environ["HIVECALL_ALLOW_DATASET_CLOUD"] = cloud_setting
    validate_excluded_runs([])
    try:
        validate_excluded_runs(["same", "same"])
    except SystemExit:
        pass
    else:
        raise AssertionError("duplicate --exclude-run-id values were accepted")
    sample = all_moments(read_records(HERE / "fixtures/minimal.jsonl"))
    assert rule_label(sample[0], 1) == "PASS"
    assert rule_label(sample[1], 2) == "FAIL"
    assert rule_label(sample[1], 2, "continue checking") == "PASS"
    assert rule_label(sample[2], 3) is None
    assert rule_label({"behavior": 3, "fixedCheck": {"label": "open"}}, 3) == "FAIL"
    assert candidate_rule_label(sample[1], 2, "Do not tick until QA evidence is recorded") is None
    assert clef_probability_label(0.01) == ("FAIL", 0.99)
    assert score_labels(["PASS", "UNKNOWN", "FAIL"]) == 50
    assert replayable_moment(sample[2])
    live_control = {**sample[2], "fixedCheck": {**sample[2]["fixedCheck"], "liveWorkerCount": 1}}
    assert replayable_moment(live_control)
    assert "active worker" in behavior_criterion(3, True, b3_evaluator_facts(live_control))
    assert "no worker is live" in behavior_criterion(3, True, b3_evaluator_facts(sample[2]))
    b3_sample, b3_counts = select_sample([sample[2], live_control], 2, 4)
    assert b3_counts[3] == 2 and {m["fixedCheck"]["liveWorkerCount"] for m in b3_sample} == {0, 1}
    assert not eval_count_shortfalls([2], {1: 0, 2: 126, 3: 11}, {1: 0, 2: 120, 3: 6})
    assert eval_count_shortfalls([3], {1: 0, 2: 126, 3: 11}, {1: 0, 2: 120, 3: 6}) == [
        "target behavior 3 has only 6 held-out moments"]
    assert not replayable_moment({"behavior": 3, "context": "work is open", "fixedCheck": {"gapMinutes": 45}})
    assert baseline_moment({"behavior": 3, "context": "no visible gap", "fixedCheck": {"gapMinutes": 45}})
    assert not baseline_moment({"behavior": 3, "fixedCheck": {"gapMinutes": 29}})
    assert replayable_moment({"behavior": 4, "actualNextAction": {"eventType": "item/started", "status": "pending"}})
    assert not replayable_moment({"behavior": 6, "actualNextAction": {"eventType": "item/delegation/completed", "status": "completed"}})
    assert len(select_sample(sample, 30, 4)[0]) == 3
    with tempfile.TemporaryDirectory() as temp:
        skill_dir = Path(temp) / "candidate"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text("fixture skill", encoding="utf-8")
        assert skill_file_from_dir(skill_dir, "--current") == skill_dir / "SKILL.md"
        try:
            skill_file_from_dir(temp, "--proposed")
        except SystemExit as exc:
            assert "must contain SKILL.md" in str(exc)
        else:
            raise AssertionError("skill directory without SKILL.md was accepted")
    assert paired_bootstrap(["PASS", "FAIL"], ["PASS", "PASS"], 1)["deltaPoints"] == 50
    weak_fixture = ("- Only the orchestrator ticks items, and only on independent proof: QA evidence.\n"
                    "3. **Tick** items proven by independent evidence. Commit locally.\n")
    weak_fixture = weaken_proof_skill(weak_fixture)
    assert "Only the orchestrator ticks" not in weak_fixture and "**Tick** items proven" not in weak_fixture
    assert "3. Commit locally." in weak_fixture
    assert eval_report_paths(argparse.Namespace(report_tag="weakened-vs-current"))[0].name == "eval-weakened-vs-current.md"
    assert calibration([{"tier": "tier2", "tierTruth": "PASS", "clef": "PASS", "judge": "FAIL"}])[
        "clef"]["tier2"]["TPR"] == 1.0
    print("PRECHECK: replay parser/rules/sample, optional exclusions, and cloud opt-in passed")


def main():
    global RUNTIME
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("baseline")
    p.add_argument("--dataset", default=str(DATASET))
    p.add_argument("--skill", default=str(CURRENT_SKILL))
    p.add_argument("--per-behavior", type=int, default=30)
    p.add_argument("--seed", type=int, default=20261016)
    p.add_argument("--exclude-run-id", action="append", default=[])
    add_runtime_options(p)
    e = sub.add_parser("eval")
    e.add_argument("--dataset", default=str(DATASET))
    e.add_argument("--current", required=True, help="current skill directory containing SKILL.md")
    e.add_argument("--proposed", required=True, help="proposed skill directory containing SKILL.md")
    e.add_argument("--targets", type=parse_targets, required=True, help="comma-separated behavior numbers targeted by the proposal")
    e.add_argument("--build-week", default=dt.datetime.now(dt.timezone.utc).strftime("%G-W%V"))
    e.add_argument("--model", default="deepseek-v4-pro")
    e.add_argument("--judge-model", default="kimi-k3")
    e.add_argument("--per-behavior", type=int, default=30)
    e.add_argument("--seed", type=int, default=20261016)
    e.add_argument("--exclude-run-id", action="append", default=[])
    e.add_argument("--report-tag", type=parse_report_tag, help="filename-safe suffix to preserve separate eval reports")
    add_runtime_options(e)
    sub.add_parser("self-check")
    args = parser.parse_args()
    if args.command == "baseline":
        RUNTIME = CallRuntime(args.cache_dir, args.max_calls)
        run_baseline(args)
    elif args.command == "eval":
        RUNTIME = CallRuntime(args.cache_dir, args.max_calls)
        run_eval(args)
    else:
        self_check()


if __name__ == "__main__":
    main()
