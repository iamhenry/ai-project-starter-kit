# Hypothesis Funnel

Use when the cause is unclear and there are several suspects.

1. List 5-7 possible sources. Cover different layers: input, state, logic, timing, config, dependency.
2. Rank them by evidence already in hand. Keep the top 1-2.
3. For each, name the smallest probe that tells them apart: a log line, an assertion, one input change.
4. Run the probes. Mark each hypothesis confirmed, refuted, or still a guess.
5. If both are refuted, go back to step 1 with the new evidence. Do not stretch a guess to fit.

Done when one cause is confirmed and the others are ruled out.
