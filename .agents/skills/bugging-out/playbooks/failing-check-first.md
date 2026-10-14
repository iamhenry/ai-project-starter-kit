# Failing Check First

Use before any fix that is not the fast lane. A check that cannot fail proves nothing.

1. Shrink the repro to the fewest steps that still fail every time. Add data if the bug only shows at scale.
2. Turn it into a rerunnable check that sees what the user sees: an output, a screen, a measured value. This is a probe, not a committed test; add the regression test only after the fix is proven.
3. Run the check on the unfixed code. It must fail. If it passes, it is too weak; make it stricter.
4. Fix. Run the same check. It must pass.
5. For flaky or timing bugs, run it several more times.

Done when the same check fails before the fix and passes after it.
