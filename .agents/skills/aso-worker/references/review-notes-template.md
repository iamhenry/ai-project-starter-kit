# App Review notes

Fills App Store Connect's "Notes" field. Max 4,000 characters. No passwords, tokens, or personal data here; demo credentials go only in the Sign-In fields.

## Check first, never overwrite silently

1. Get the editable version ID: `asc status --app "$APP_ID"`.
2. Read it: `asc review details-for-version --version-id "$VERSION_ID"` (no `--include-sensitive`).
3. Then:
   - **Empty or no record:** draft below, show the user, write only after approval: `asc review details-create --version-id "$VERSION_ID" --notes "$(cat <draft>)"`.
   - **Notes exist** (often copied from last release): show old and new side by side and ask: keep, replace, or merge. Recommend keep unless the shipped diff makes it stale. Write nothing until they answer.
   - **Updating:** pass only `--notes`. Never touch contact or demo-account flags unless asked.
4. Read it back and confirm it matches the approved text.

## Draft

Fill from the shipped diff and the real app. Drop lines that don't apply. Aim for under 1,500 characters.

```
What changed: [One sentence. Metadata-only: "No functional changes; only App Store text updated."]
Sign-in: [No account needed. | Demo credentials are in the Sign-In fields.]
Quick test (about 2 min):
1. [Launch step or onboarding to skip.]
2. [Core action.]
3. [Expected result.]
4. [Changed or gated feature, and where to find it.]
Settings: [Permission prompts and that Deny is safe; purchases and Restore location; hardware, region, or network needs. Or "None."]
Looks broken but isn't: [Or "None."]
```
