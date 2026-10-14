# Compare Good and Bad

Use when it used to work, or works in one place and not another.

1. Name one good case and one bad case: a commit, branch, device, input, setting, or package version.
2. List every difference: code, config, data, environment, dependencies, and the steps taken.
3. Apply half the differences to the good case and see which side it lands on. Use `git bisect` for commits.
4. Repeat until one difference flips good to bad.
5. Confirm by applying only that difference to the good case. It must break.

Done when a single difference reliably turns good into bad.
