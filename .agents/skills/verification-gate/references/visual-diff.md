# Verification Gate: Visual Convergence Loop

Use when the task changes visible UI against a reference design or ideal-state screenshot.

1. Capture a baseline of the target screen at or before the current state.
2. Run the platform pixel diff against the ideal state: `agent-browser diff screenshot --baseline <before.png> -o diff.png` (web, desktop), or argent `screenshot-diff` (iOS, Android).
3. If the changed-pixel ratio exceeds the declared tolerance, the diff image names where to fix next. Route that back to implementation and re-diff after the fix.
4. Stop when the ratio is within tolerance or the remaining diffs are declared acceptable (for example font-version rendering). Record the final ratio and diff image as Observable evidence.

Tolerance is set by the Verification Target, not invented here. The diff image supports the verdict; it never replaces the Primary Flow proof.
