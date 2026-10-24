# Benchmark task: Pro To-Do App

Only the sections marked "Run rules" are specific to this run; everything else is the product spec.

## Goal
Build a pro-level to-do app with `index.html`, `style.css`, and `app.js`. You may split the code into more `.js` or `.css` files if that helps the team work in parallel. Use plain HTML, CSS, and JS only: no libraries, packages, CDNs, or build step. The only exception is Google Fonts. Use native browser features, for example `<input type="date">`, HTML5 drag and drop, localStorage, IndexedDB, BroadcastChannel, the Notification API, `<canvas>`, and `<dialog>`. Style it using `design.md`. Opening `index.html` directly in a browser must work.

## Features

### Core (from before)
1. **Add:** Enter or the Add button. Blank input is ignored.
2. **Complete:** a checkbox toggles done, and done items show crossed out.
3. **Delete:** deleted items go to the Trash (see #29).
4. **Edit:** double-click to edit. Enter saves, Escape cancels, and saving empty text deletes the item.
5. **Drag and drop:** reorder items. The order persists.
6. **Filters:** All / Active / Done / Due today.
7. **Counter and clear:** "N items left" plus a "Clear done" button.
8. **Persistence:** everything survives a page refresh.
9. **Keyboard:** arrow keys move between items, Space toggles, Delete removes, and the focus ring is visible.
10. **Sub-tasks:** one level deep. A parent counts as done only when all its children are done.
11. **Import/export:** export and import JSON. Invalid files are rejected with a visible message, and existing data stays untouched.
12. **Due dates:** set with the native date picker. Overdue items are visibly marked, in grayscale.

### New
13. **Calendar views:** month and week views. Drag tasks between days to change their due date. In week view, resize a task to change its duration.
14. **Multiple lists:** create, rename, and delete lists, and move tasks between them. Each list gets a grayscale shade.
15. **Recurring tasks:** daily, weekly, monthly, or custom (for example, "every 2nd Tuesday"). Completing one creates the next.
16. **Undo and redo:** Ctrl/Cmd+Z and Ctrl/Cmd+Shift+Z for every action in the app.
17. **Sync between tabs:** changes appear live in other open tabs.
18. **Tags:** add tags, click a tag to filter, and rename a tag everywhere.
19. **Priorities:** P1–P3, sortable, and shown in the calendar and board.
20. **Search:** across all lists, tags, and notes, with matches highlighted.
21. **Notes:** each task has notes with simple formatting (bold, links, checklists), written by hand with no library.
22. **Attachments:** drag an image onto a task to attach it. Store it in IndexedDB and show a preview.
23. **Reminders:** browser notifications when a task comes due, if the user grants permission.
24. **Time tracking:** start and stop a timer on a task, with totals shown per task and per list.
25. **Command palette:** Cmd/Ctrl+K opens it. Type the name of an action to run it.
26. **Board view:** kanban columns (To do / Doing / Done) with drag and drop, kept in sync with the list view.
27. **Stats page:** tasks completed per day, drawn as a hand-built `<canvas>` chart.
28. **Views switcher:** List / Board / Calendar / Stats, and the current view persists.
29. **Trash:** deleted items can be restored or permanently emptied.

## Definition of done
- All 29 features work in a real browser, with no console errors.
- Features work together. For example: undo after moving a task on the calendar; completing a recurring task in board view; a tag rename showing up in search; a change in one tab appearing in another.
- Styling follows the Do's and Don'ts in `design.md` section 7.
- Every feature is marked signed off in `tasks.md` by an agent who did NOT build it.

Out of scope: accounts, backend, dark mode, touch drag on mobile, print view, share links, anything beyond Google Fonts.

## Run rules (hivecall benchmark, new)
- **Ledger:** `checklist.html`, one item per feature (ISC-1 … ISC-29, same numbers as above). It replaces `tasks.md`; a fresh tester's PASS line with evidence is the sign-off by "an agent who did NOT build it".
- **No owner.** Nobody answers questions during the run. Use your best judgment, write the assumption in the run card, and keep going. A question only the owner can answer is parked with its reason; it never stops other work.
- **#23 Reminders:** if the browser will not grant notification permission, grant it in the test browser if you can; otherwise park #23 with the exact blocker and move on.
- **Time cap: 2 hours** from the hivecall skill load. At the cap, finish nothing new: record every open item as FAIL or BLOCKED with its reason, write the run card's `## Final report`, set `status: closed`.
- **Git:** local commits only. Never push, never open a PR.
- **Safety:** stay inside this folder. No packages. No network except Google Fonts in the page.
- **Do not read** anything outside this folder about earlier runs of this task.
