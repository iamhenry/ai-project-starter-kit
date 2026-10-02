# Web

Desktop browser, pointer and keyboard. Start from `assets/starter-web.html`. Verify at 1440 × 900, then at a narrow width to check reflow.

No touch gestures and no use-gesture in this domain. Input is pointer, keyboard, and scroll.

## Layout

- Content width capped (about 1200 px) and centered; use the space for side-by-side context rather than stretching text.
- App-style prototypes: persistent sidebar on wide screens (`drawer lg:drawer-open`), collapsing to a drawer on narrow screens. Page-style prototypes: top navigation with sections.
- Multi-panel layouts (list and detail, editor and inspector) are often the right shape on desktop; avoid phone-style single-column flows.
- Responsive reflow down to tablet and phone widths without horizontal overflow.

## Interaction

- **Keyboard:** logical tab order, visible focus, Enter and Space activate, Esc closes overlays. Add shortcuts only for frequent actions and show them where the action lives.
- **Pointer:** hover may reveal secondary actions, but every action is reachable without hover. Cursor reflects affordance (`pointer`, `grab`, `text`).
- **Drag and drop** where the product needs it (reorder, move between columns, upload): pointer events with a visible drop target and a keyboard alternative.
- **Context menus and popovers** anchored to their trigger; dialogs centered with `showModal()`.
- **Toasts** bottom-right or top-center, never covering primary content.

## Motion on web

Subtler than mobile: fades and short slides for panels and dialogs, quick feedback on press. Hover transitions only if the design allows them.
