# Tight Loop

Instrumented hill climbing. Fits when the cause seems near and each check takes seconds or minutes.

1. Get the cheapest repro that shows the bug every time. Grow it only if the cheap one can't.
2. Add the fewest logs that test the current guess: event order, IDs, inputs, outputs.
3. Run, read, adjust the guess. Keep each run short so rounds stay fast.
4. Make the smallest fix the evidence supports.
5. Rerun the same repro fresh. The bug must be gone; then remove the logs.

Stalls when runs stop changing your guess. Switch to another playbook.
