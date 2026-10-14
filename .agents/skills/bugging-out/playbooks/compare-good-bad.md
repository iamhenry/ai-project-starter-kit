# Compare Good and Bad

Fits when a working version exists: a commit, branch, device, input, setting, or package version.

1. Pin one good case and one bad case.
2. List the differences: code, config, data, environment, dependencies, steps taken.
3. Move half the differences to the good case and see which side it lands on. `git bisect` does this for commits.
4. Repeat until one difference flips good to bad.
5. Confirm by moving only that difference. It must break the good case.

Done when one difference reliably flips good to bad.
