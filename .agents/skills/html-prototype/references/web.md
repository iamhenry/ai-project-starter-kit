# Web

Desktop-first browser experience, responsive by default. Start from `assets/starter-web.html`. Verify at 1440 × 900, 1024 × 768, and 390 × 844.

Input is pointer, keyboard, and scroll. No touch gestures (swipe, edge swipe, pinch) in this domain; pointer drag and drop is fine.

## Responsive by default

Every web prototype works from phone to wide desktop without horizontal scrolling.

| Width | Layout |
|---|---|
| Desktop (≥ 1024 px) | Persistent sidebar (`drawer lg:drawer-open`) or top navigation; multi-panel layouts side by side. |
| Tablet (768 to 1023 px) | Sidebar collapses to a drawer opened from the top bar; panels may stay side by side if they fit. |
| Phone (< 768 px) | Single column; panels stack; dialogs stay centered and fit the screen. |

- Content width capped (about 1200 px) and centered. Use the space for side-by-side context rather than stretching text.
- Tables and dense grids get a narrow-screen form (cards or a horizontal scroll inside their own container), never page-level overflow.
- Keyboard shortcuts are a desktop bonus; every action stays reachable by tap on narrow screens.

## Layout

- App-style prototypes: sidebar plus content. Page-style prototypes: top navigation with sections.
- Multi-panel layouts (list and detail, editor and inspector) are often the right shape on desktop; avoid phone-style single-column flows at desktop widths.

## Interaction

- **Keyboard:** logical tab order, visible focus, Enter and Space activate, Esc closes overlays. Add shortcuts only for frequent actions and show them where the action lives.
- **Pointer:** hover may reveal secondary actions, but every action is reachable without hover. Cursor reflects affordance (`pointer`, `grab`, `text`).
- **Drag and drop** where the product needs it (reorder, move between columns, resize): interact.js with a visible drop target and a keyboard alternative. See the `animation-principles` gesture reference.
- **Context menus and popovers** anchored to their trigger; dialogs centered with `showModal()`.
- **Toasts** bottom-right or top-center, never covering primary content.

## Motion on web

Follow the `animation-principles` skill. Desktop motion is subtler than mobile: frequent keyboard and pointer actions (menus, selection, shortcuts) appear instantly; panels and dialogs get short fades or slides.
