# Refine Checklist

Use this when improving an existing worker.

## 1. Closure

- Did any action depend on a human?
- Did any required tool prove missing or unreliable?
- Did the worker fail to verify its own actions?

If yes, the loop is open again. Fix closure first.

## 2. Score quality

- Is the worker improving the intended outcome?
- Is it gaming the metric?
- Is the main score too slow, noisy, or delayed?
- Do we need a better leading indicator?

## 3. Execution quality

- Are actions too broad or too risky?
- Is the worker choosing high-leverage actions?
- Is it stuck repeating low-value work?
- Are the operating principles leading to good decisions? Should any be updated?

## 4. Memory quality

- Are learnings being recorded clearly?
- Can the next cycle pick up without guessing?
- Are failures and dead ends preserved?

## 5. Safety

- Were any hard stops hit?
- Are budgets or rate limits too loose?
- Do escalation triggers need tightening?

## 6. Tighten the worker

Update only what improves autonomy:

- score
- verification surface
- action-to-tool map
- safety limits
- memory paths
