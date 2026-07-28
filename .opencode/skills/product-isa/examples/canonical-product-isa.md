---
artifact: product-isa
format: lifeos-inspired
title: "OneNote"
status: ready
clarification_progress: 8/8
principal_stated_goal: "I want one simple note on my iPhone that I can write or change without an account or internet, and it must still be there when I come back."
created: 2026-07-28
updated: 2026-07-28
progress: 0/27
---

# Product ISA: OneNote

## Problem

Capturing one durable note should not require account setup, connectivity, or organizing a larger notes system.

## Vision

A person opens the app, writes or edits one note, and returns later to the latest saved text. Empty, edit, offline, read-failure, and save-failure states remain clear and user-controlled.

## Out of Scope

- Multiple notes, folders, formatting, attachments, accounts, sharing, and synchronization.
- Automatic changes to saved text.

## Constraints

- Creating, editing, and reopening the note work without a connection.
- No account or sign-in is required.
- Saving and reopening the note initiate no network request.

## Goal

A person can create, read, and edit one persistent plain-text note on an iPhone without an account or internet, while cancellation, invalid input, and read or save failures never misrepresent or silently change the saved note.

## Criteria

- [ ] ISC-001: An empty Home screen shows "No note yet".
- [ ] ISC-002: An empty Home screen shows exactly one Add Note action.
- [ ] ISC-003: Creating a valid note shows the submitted text on Home.
- [ ] ISC-004: The latest saved note remains after relaunch.
- [ ] ISC-005: Canceling an edit leaves the saved note unchanged.
- [ ] ISC-006: Blank or whitespace-only text cannot be saved.
- [ ] ISC-007: The Editor shows a Note text field.
- [ ] ISC-008: The Editor shows a Save action.
- [ ] ISC-009: The Editor shows a Cancel action.
- [ ] ISC-010: Editing an existing note preloads its saved text.
- [ ] ISC-011: A saved-note read failure shows "Couldn't load your note."
- [ ] ISC-012: A saved-note read failure shows a Retry action.
- [ ] ISC-013: Anti: A saved-note read failure shows the empty-note message.
- [ ] ISC-014: A note created offline remains after an offline relaunch.
- [ ] ISC-015: No offline warning appears during offline core flows.
- [ ] ISC-016: Anti: Account creation or sign-in blocks the core flow.
- [ ] ISC-017: Anti: Creating, editing, or reopening a note initiates a network request.
- [ ] ISC-018: A successful Retry shows the previously saved note unchanged.
- [ ] ISC-019: A populated Home screen shows exactly one Edit Note action.
- [ ] ISC-020: Canceling a new note returns Home to its prior empty state.
- [ ] ISC-021: Saving a valid edit replaces the prior visible text.
- [ ] ISC-022: A note edited offline remains after an offline relaunch.
- [ ] ISC-023: Entering valid text after invalid input makes Save available.
- [ ] ISC-024: A failed Save shows "Couldn't save your note."
- [ ] ISC-025: Anti: A failed Save changes the durable note state.
- [ ] ISC-026: A failed Save shows a Retry action.
- [ ] ISC-027: A successful Save Retry applies the pending valid text exactly once.

## Test Strategy

| ISC | Anchors to | Source contracts | Probe type | Check | Pass threshold | Tool |
| --- | --- | --- | --- | --- | --- | --- |
| ISC-001 | derived: clear empty state | SCR-001, DATA-002 | appearance | Open with no saved note | "No note yet" is visible | Screenshot plus UI assertion |
| ISC-002 | derived: one clear empty-state action | SCR-001, DATA-002 | appearance | Open with no saved note | Exactly one Add Note action is visible | UI assertion |
| ISC-003 | literal | FTR-001, FLOW-001, ACT-001, DATA-001 | behavioral | Add "Buy oats" and Save | Home shows "Buy oats" | iOS UI automation |
| ISC-004 | literal | FTR-001, ACT-001, ACT-002, DATA-001 | persistence | Save "Buy oats", terminate, and relaunch | Home still shows "Buy oats" | iOS UI automation |
| ISC-005 | derived: user controls edits | FTR-002, FLOW-002, ACT-004, EDGE-003 | regression | Replace "Buy oats" with whitespace and Cancel | Home still shows "Buy oats" | iOS UI automation |
| ISC-006 | derived: invalid input cannot mutate state | FTR-001, SCR-002, ACT-001, ACT-002, EDGE-003 | validation | Enter whitespace in create mode and edit mode | Save is unavailable in both modes and prior state is unchanged | iOS UI automation |
| ISC-007 | derived: editor anatomy | SCR-002 | appearance | Open the Editor | One Note text field is visible | UI assertion |
| ISC-008 | derived: editor anatomy | SCR-002 | appearance | Open the Editor | One Save action is visible | UI assertion |
| ISC-009 | derived: editor anatomy | SCR-002 | appearance | Open the Editor | One Cancel action is visible | UI assertion |
| ISC-010 | derived: safe editing context | FTR-002, SCR-002, FLOW-002 | behavioral | Save "Buy oats" and open Edit Note | The Note field contains "Buy oats" | iOS UI automation |
| ISC-011 | derived: honest load failure | SCR-001, FLOW-003, ACT-005, EDGE-002 | recovery | Open while the saved-note read is forced to fail | "Couldn't load your note." is visible | Controlled failure UI test |
| ISC-012 | derived: recoverable load failure | SCR-001, FLOW-003, ACT-005, EDGE-002 | recovery | Open with a forced read failure, then Retry while the read still fails | One Retry action remains visible after the repeated failure | Controlled failure UI test |
| ISC-013 | derived: never misrepresent failure as empty | SCR-001, FLOW-003, ACT-005, DATA-001, DATA-002, EDGE-002 | safety | Open while the saved-note read is forced to fail | "No note yet" is absent | Controlled failure UI test |
| ISC-014 | literal | FTR-001, FLOW-001, ACT-001, DATA-001, EDGE-001 | offline persistence | Disable networking, create "Buy oats", terminate, and relaunch offline | Home shows "Buy oats" | Network-disabled iOS UI automation |
| ISC-015 | derived: offline is a normal operating state | FLOW-001, EDGE-001 | appearance | Complete create, edit, and relaunch while offline | No offline warning appears | Network-disabled UI assertion |
| ISC-016 | literal | FLOW-001, FLOW-002 | access | Launch fresh and complete create and edit | No account or sign-in gate appears | iOS UI automation |
| ISC-017 | literal | ACT-001, ACT-002, EDGE-001 | network | Create, edit, terminate, and reopen the note | Zero outbound network requests occur | Network capture |
| ISC-018 | derived: recovery preserves saved state | FLOW-003, ACT-005, DATA-001, EDGE-002 | recovery | Save "Buy oats", force one read failure, then allow Retry to succeed | Home shows "Buy oats" unchanged | Controlled failure UI test |
| ISC-019 | derived: populated-state action | SCR-001 | appearance | Open with "Buy oats" saved | Exactly one Edit Note action is visible | UI assertion |
| ISC-020 | derived: create cancellation is non-mutating | FLOW-001, ACT-003, DATA-002, EDGE-003 | regression | Open Add Note, enter whitespace, and Cancel | Home shows "No note yet" | iOS UI automation |
| ISC-021 | derived: saved edits replace prior text | FTR-001, FLOW-002, ACT-002, DATA-001 | behavioral | Change "Buy oats" to "Buy milk" and Save | Home shows "Buy milk" and not "Buy oats" | iOS UI automation |
| ISC-022 | literal | FTR-001, FLOW-002, ACT-002, DATA-001, EDGE-001 | offline persistence | Disable networking, change "Buy oats" to "Buy milk", terminate, and relaunch offline | Home shows "Buy milk" | Network-disabled iOS UI automation |
| ISC-023 | derived: invalid input is recoverable | EDGE-003 | validation | In create mode and edit mode, enter whitespace and then replace it with valid text | Save changes from unavailable to available in both modes | iOS UI automation |
| ISC-024 | derived: honest save failure | SCR-002, FLOW-001, FLOW-002, ACT-001, ACT-002, EDGE-004 | recovery | Force a valid Save to fail | "Couldn't save your note." is visible | Controlled failure UI test |
| ISC-025 | derived: failed saves preserve durable state | FTR-001, FLOW-001, FLOW-002, ACT-001, ACT-002, DATA-001, DATA-002, EDGE-004 | safety | Force one create Save and one edit Save to fail, then relaunch | Create leaves Home empty; edit leaves the prior saved text unchanged | Controlled failure persistence test |
| ISC-026 | derived: save failure is recoverable | SCR-002, FLOW-001, FLOW-002, ACT-001, ACT-002, EDGE-004 | recovery | Force a valid Save to fail | One Retry action is visible | Controlled failure UI test |
| ISC-027 | derived: save retry applies pending intent once | FTR-001, FLOW-001, FLOW-002, ACT-001, ACT-002, DATA-001, EDGE-004 | recovery | Fail one create Save and one edit Save, then allow each Retry to succeed | Each pending text appears exactly once and is the durable note after relaunch | Controlled failure UI test |

## Features

This section is the detailed product contract for this Product ISA, not an implementation plan.

### Feature Catalog

#### FTR-001: Maintain one note
Status: Active
Purpose: Preserve one piece of plain text with minimal friction.
Required behavior:
- Saving valid text creates the note or replaces its prior text.
- The latest saved text survives relaunch.
- Blank or whitespace-only text cannot be saved.
- A failed Save leaves durable note state unchanged until a Retry succeeds.
Inputs and outputs: Plain text in; one visible saved note out.
Related surfaces: SCR-001, SCR-002
Related flows: FLOW-001, FLOW-002
Satisfies: ISC-003, ISC-004, ISC-006, ISC-014, ISC-021, ISC-022, ISC-025, ISC-027

#### FTR-002: Cancel an edit safely
Status: Active
Purpose: Let the user leave an edit without changing saved text.
Required behavior:
- Edit mode begins with the saved text preloaded.
- Cancel leaves the saved note unchanged.
Inputs and outputs: Existing note in; either unchanged or explicitly saved text out.
Related surfaces: SCR-001, SCR-002
Related flows: FLOW-002
Satisfies: ISC-005, ISC-010

### Screen Contracts

#### SCR-001: Home
Status: Active
Purpose: Show the current note state and one relevant primary action.
Entry and exit: Opens at launch; Add Note or Edit Note opens SCR-002.
Required elements:
- Empty state shows "No note yet" and exactly one Add Note action.
- Populated state shows the saved text and exactly one Edit Note action.
- Read failure shows the load error and Retry, never the empty state.
States: Empty, populated, and load failure.
Serves: FTR-001, FTR-002
Satisfies: ISC-001, ISC-002, ISC-003, ISC-011, ISC-012, ISC-013, ISC-019, ISC-021

#### SCR-002: Editor
Status: Active
Purpose: Create or edit the note.
Entry and exit: Add Note opens empty mode; Edit Note opens prefilled mode; Save or Cancel returns Home.
Required elements:
- One Note text field.
- One Save action.
- One Cancel action.
States: Save is unavailable for blank or whitespace-only text; edit mode preloads saved text; Save failure follows EDGE-004.
Serves: FTR-001, FTR-002
Satisfies: ISC-006, ISC-007, ISC-008, ISC-009, ISC-010, ISC-024, ISC-026

### User Flow Contracts

#### FLOW-001: Create the note
Status: Active
Trigger: Tap Add Note from empty Home.
Path: Home -> Add Note -> enter valid text -> Save -> populated Home.
Branches and recovery: Blank text cannot be saved; Cancel returns to the prior empty state; offline behavior is unchanged and shows no warning; Save failure follows EDGE-004.
End state: Home shows the submitted text.
Uses: FTR-001, SCR-001, SCR-002, ACT-001, ACT-003
Satisfies: ISC-002, ISC-003, ISC-006, ISC-014, ISC-015, ISC-016, ISC-020, ISC-024, ISC-025, ISC-026, ISC-027

#### FLOW-002: Edit the note
Status: Active
Trigger: Tap Edit Note from populated Home.
Path: Home -> Edit Note -> preloaded text -> change text -> Save -> updated Home.
Branches and recovery: Blank text cannot be saved; Cancel leaves the prior text unchanged; offline behavior is unchanged; Save failure follows EDGE-004.
End state: Home shows only the latest explicitly saved text.
Uses: FTR-001, FTR-002, SCR-001, SCR-002, ACT-002, ACT-004
Satisfies: ISC-005, ISC-006, ISC-010, ISC-015, ISC-016, ISC-021, ISC-022, ISC-024, ISC-025, ISC-026, ISC-027

#### FLOW-003: Recover a failed read
Status: Active
Trigger: The saved note cannot be read at launch.
Path: Load error -> Retry -> populated Home after the read succeeds.
Branches and recovery: Failure never appears as empty; repeated failure remains on the recoverable load error.
End state: A successful Retry shows the unchanged saved note.
Uses: SCR-001, ACT-005
Satisfies: ISC-011, ISC-012, ISC-013, ISC-018

### Action Contracts

#### ACT-001: Save new note
Status: Active
Surface and trigger: SCR-002 Save in add mode.
Prerequisites: Text contains at least one non-whitespace character.
Result: Home shows the submitted text and it survives relaunch.
Validation: Save is unavailable for invalid text.
Failure and repetition: Save failure follows EDGE-004; repetition is not separately specified.
Side effects: Saved note changes; no network request.
Satisfies: ISC-003, ISC-004, ISC-006, ISC-014, ISC-017, ISC-024, ISC-025, ISC-026, ISC-027

#### ACT-002: Save edited note
Status: Active
Surface and trigger: SCR-002 Save in edit mode.
Prerequisites: Text contains at least one non-whitespace character.
Result: Home replaces the prior text and the latest text survives relaunch.
Validation: Save is unavailable for invalid text.
Failure and repetition: Save failure follows EDGE-004; repetition is not separately specified.
Side effects: Saved note changes; no network request.
Satisfies: ISC-004, ISC-006, ISC-017, ISC-021, ISC-022, ISC-024, ISC-025, ISC-026, ISC-027

#### ACT-003: Cancel new note
Status: Active
Surface and trigger: SCR-002 Cancel in add mode.
Prerequisites: Add mode is open.
Result: Home returns to its prior empty state.
Validation: None.
Failure and repetition: Not separately specified.
Side effects: None.
Satisfies: ISC-020

#### ACT-004: Cancel edited note
Status: Active
Surface and trigger: SCR-002 Cancel in edit mode.
Prerequisites: An existing note is being edited.
Result: Home shows the prior saved text unchanged.
Validation: None.
Failure and repetition: Not separately specified.
Side effects: None.
Satisfies: ISC-005

#### ACT-005: Retry saved-note read
Status: Active
Surface and trigger: SCR-001 Retry in load-failure state.
Prerequisites: The prior saved-note read failed.
Result: Success shows the unchanged saved note; failure retains the load error.
Validation: The empty state is never substituted for failure.
Failure and repetition: Retry remains available after another failed read.
Side effects: Saved text remains unchanged.
Satisfies: ISC-011, ISC-012, ISC-013, ISC-018

### Data Display Contracts

#### DATA-001: Saved note text
Status: Active
Surface: SCR-001
Source and meaning: The latest explicitly saved plain text.
Presentation: Show saved text verbatim.
Freshness and persistence: Update after Save and survive relaunch, including offline relaunch.
Privacy and unavailable states: A read failure shows EDGE-002; a Save failure preserves current text until Retry succeeds.
Satisfies: ISC-003, ISC-004, ISC-011, ISC-012, ISC-013, ISC-014, ISC-018, ISC-021, ISC-022, ISC-025, ISC-027

#### DATA-002: Empty note state
Status: Active
Surface: SCR-001
Source and meaning: No note has been saved.
Presentation: "No note yet" and exactly one Add Note action.
Freshness and persistence: Returns unchanged when new-note creation is canceled or its Save fails.
Privacy and unavailable states: Must not appear when saved data failed to load.
Satisfies: ISC-001, ISC-002, ISC-013, ISC-020, ISC-025

### Edge-State Contracts

#### EDGE-001: No network connection
Status: Active
Trigger: Create, edit, relaunch, or reopen while offline.
Impact: The Core Job would fail if connectivity were required.
Required behavior: Creating and editing remain available; saved results survive offline relaunch.
User signal: No offline warning appears.
Recovery: None required.
Must remain unchanged: Account-free access and the latest saved note.
Satisfies: ISC-014, ISC-015, ISC-016, ISC-017, ISC-022

#### EDGE-002: Saved note cannot be read
Status: Active
Trigger: A saved-note read fails at launch.
Impact: Empty state would falsely imply the note does not exist.
Required behavior: Show the load error and Retry; never show empty state.
User signal: "Couldn't load your note."
Recovery: Retry; success restores the unchanged note and failure remains recoverable.
Must remain unchanged: Saved note text.
Satisfies: ISC-011, ISC-012, ISC-013, ISC-018

#### EDGE-003: Invalid note text
Status: Active
Trigger: Editor text is empty or whitespace-only.
Impact: Saving would create a meaningless note or erase a valid one.
Required behavior: Save is unavailable.
User signal: Disabled Save action.
Recovery: Enter at least one non-whitespace character or Cancel.
Must remain unchanged: Prior Home state and saved note.
Satisfies: ISC-005, ISC-006, ISC-020, ISC-023

#### EDGE-004: Note cannot be saved
Status: Active
Trigger: Saving valid note text fails.
Impact: Reporting success or changing durable state would mislead the user or lose trusted text.
Required behavior: Show the save error and Retry; durable note state remains unchanged until Retry succeeds.
User signal: "Couldn't save your note."
Recovery: Retry the pending Save.
Must remain unchanged: Prior durable note state.
Satisfies: ISC-024, ISC-025, ISC-026, ISC-027

## Decisions

### DEC-001: Keep the core flow account-free and offline
Date: 2026-07-28
Category: Boundaries
Status: Active
Chosen: No account and no network dependency
User words:
> I want one simple note on my iPhone that I can write or change without an account or internet, and it must still be there when I come back.
Rationale: Not stated
Rejected alternatives:
- Optional account synchronization - Adds setup and connectivity outside the stated goal.
Locks:
- Source contracts: FTR-001, FLOW-001, FLOW-002, EDGE-001
- Criteria: ISC-004, ISC-014, ISC-015, ISC-016, ISC-017, ISC-022

### DEC-002: Cancellation never saves draft text
Date: 2026-07-28
Category: Actions
Status: Active
Chosen: Cancel restores the prior Home state
User words:
> If I hit Cancel, I expect nothing I typed in that editor to replace my note.
Rationale: Not stated
Rejected alternatives:
- Auto-save editor changes - Removes explicit user control over when text becomes durable.
Locks:
- Source contracts: FTR-002, FLOW-001, FLOW-002, ACT-003, ACT-004
- Criteria: ISC-005, ISC-020
