---
name: five-whys
description: Root cause analysis for software bugs using the 5 Whys technique. Use when the user wants to find the underlying cause of a bug, error, or technical issue. Triggers include phrases like "why is this happening", "root cause", "debug this", or when investigating software problems.
---

# 5 Whys Debugging

Ask successive evidence-backed "why" questions to find the root cause of a bug. Five is a reminder to look beneath symptoms, not a required round count.

---

## ⛔ CRITICAL: One Why at a Time

**ANTI-PATTERN (DO NOT DO THIS):**
- Asking all 5 whys in a single response
- Hypothesizing answers without code evidence
- Jumping to conclusions before investigating

**CORRECT PATTERN:**
```
ASK why #1 → STOP → INVESTIGATE → ANSWER with evidence
     ↓
ASK why #2 only if it can distinguish the remaining cause
     ↓
... continue only while the next why narrows the causal chain
```

You MUST search the codebase and gather evidence between each "why" question. If you find yourself typing "WHY #2" without having investigated after "WHY #1", you are doing it wrong.

---

## Investigation Techniques

Evidence gathering is the core of each "why" iteration. Use these approaches flexibly — they're starting points, not checklists.

### Trace the Data Flow
Follow the FULL value through the system to find where behavior diverges from expectation:
- Origin → transformations → failure point
- Dependencies, imports, function calls
- State changes across boundaries (API, DB, modules, etc)

### Examine Artifacts
Look at anything that might hold evidence:
- Logs, error messages, stack traces
- Git history near the failure (`git log -p`, `git blame`)
- Configs, environment settings, feature flags
- Runtime state, API responses, database records
- Tests, comments, documentation

This isn't exhaustive — follow whatever trail the problem reveals.

### When Stuck
- Ask the user for additional context
- State what evidence you need and why
- Never fabricate evidence or guess at causation

---

## Process

> ⚠️ **CRITICAL RULES**
> - After each "why" question, WAIT for investigation results before moving to the next
> - Test one causal hypothesis with the smallest safe discriminating probe per round
> - Never ask multiple whys in one response
> - All answers must cite specific files, lines, or logs as evidence

Work through this ONE step at a time. Do not skip ahead.

1. State the current symptom/problem
2. Ask "Why did this happen?"
3. ⛔ **STOP AND INVESTIGATE** - Search the codebase, read files, check logs. Do NOT continue until you have code evidence.
4. Present findings and the answer to "why"
5. Ask the next "Why?" only when it can distinguish the current explanation from a plausible alternative
6. ⛔ **STOP AND INVESTIGATE** - Same techniques, deeper layer. Do NOT continue without evidence.
7. Repeat steps 4-6 until an exit criterion is met:
   - `PROVEN`: evidence identifies an actionable cause; stop
   - `REJECTED`: evidence disproves the current hypothesis; continue only with one evidence-supported next hypothesis
   - `BLOCKED`: required evidence or access is unavailable; stop and name the unlock condition
   - `EXHAUSTED`: another "why" would be speculation or would not change the action; stop and report what remains unknown
   - Never make up evidence or fabricate a root cause
8. Present findings in this format:

Example: if evidence proves expired-session handling is the actionable defect,
stop there unless the task explicitly asks why that handling was omitted.

```
**Problem**
[Clear description of what appears broken vs what's actually happening]

**Root Cause**
[The underlying reason - reference specific commits, files, lines when known]

**Result**
`PROVEN|REJECTED|BLOCKED|EXHAUSTED`

**Reproduction Scenarios**
[Step-by-step scenarios showing how the bug manifests, with actual values/logs]

**Proposed Fix Locations:**
| Priority | Location | Fix |
|----------|----------|-----|
| P0 | file:line | Description of what to change |
| P1 | file:line | Description of what to change |

**Potential Solutions:**
| # | Solution | Confidence | Complexity | Description |
|---|----------|------------|------------|-------------|
| 1 | Brief name | X% | Low/Medium/High | Detailed explanation |
| 2 | Brief name | Y% | Low/Medium/High | Detailed explanation |
| 3 | Brief name | Z% | Low/Medium/High | Detailed explanation |

**Critical rules:**
- After each "why" question, WAIT for investigation results before moving to the next question
- Never ask multiple whys in one response
- All solutions must be grounded in evidence found during investigation
- If confidence is below 50%, explain what additional evidence is needed
```

---

## Example Flow

```
**Starting symptom:** App crashes when user clicks submit

**Round 1:**  
Question: "Why does it crash?"  
Investigation: Check error logs  
Evidence: `NullPointerException at line 47`  
Answer: Null pointer exception

**Round 2:**  
Question: "Why is there a null pointer?"  
Investigation: Check what's null at line 47  
Evidence: Variable `currentUser` is null  
Answer: The user object is null

**Round 3:**  
Question: "Why is the user object null?"  
Investigation: Check where `currentUser` comes from  
Evidence: `getSession().getUser()` returns null  
Answer: The session doesn't have a user

**Round 4:**  
Question: "Why doesn't the session have a user?"  
Investigation: Check session state  
Evidence: Session token expired 2 hours ago  
Answer: The session expired

**Round 5:**  
Question: "Why did it expire without handling it?"  
Investigation: Check session management code  
Evidence: No refresh logic exists, no expiry handling  
Answer: Session refresh was never implemented

---

**Problem**
The app crashes with a NullPointerException when users click submit, but the actual issue is not a null check problem. The session token expires after 30 minutes, yet the user object is retrieved without verifying session validity first.

**Root Cause**
Commit a4b8c1d added submit functionality but didn't include session management. The authentication middleware at auth.ts:45 creates sessions but has no refresh mechanism. When sessions expire, getSession().getUser() at handler.ts:47 returns null.

**Reproduction Scenarios**

Scenario A: User submits within 30 minutes
- Login → create session → user clicks submit within 30min
- Session valid → getSession().getUser() returns user object ✓
- Result: Works fine

Scenario B: User submits after 30 minutes  
- Login → create session → user waits 31 minutes → clicks submit
- Session expired → getSession().getUser() returns null
- Line 47 tries to access null.id → NullPointerException ✗
- Result: Crash

**Proposed Fix Locations:**
| Priority | Location | Fix |
|----------|----------|-----|
| P0 | auth.ts:45 | Add session refresh token logic |
| P1 | middleware.ts:22 | Add session expiry check before request processing |
| P2 | config.ts:8 | Increase session timeout from 30min to 2hr |

**Potential Solutions:**
| # | Solution | Confidence | Complexity | Description |
|---|----------|------------|------------|-------------|
| 1 | Implement automatic session refresh | 85% | Medium | Add token renewal 5 minutes before expiry. Maintains user session seamlessly without re-login |
| 2 | Add expiry detection and graceful redirect | 75% | Low | Check session validity before submit, redirect to login if expired with message. Simple but interrupts user |
| 3 | Extend timeout and add null checks | 40% | Low | Band-aid solution - increases timeout to 24hrs and adds defensive null handling. Doesn't solve underlying issue |
```

---

## Tips

- Ask ONE "why" at a time, then investigate
- Gather concrete evidence before answering (logs, code, configs)
- If you can't find evidence, ask the user for help - don't guess
- Stop when you find something actionable to fix
- Each "why" digs deeper into the same chain - don't branch sideways
- The root cause should be something you can actually change
- Be honest if you can't reach a definitive root cause - uncertainty is better than making things up
