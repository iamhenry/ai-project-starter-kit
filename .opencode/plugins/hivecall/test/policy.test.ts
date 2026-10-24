import { afterEach, describe, expect, test } from "bun:test"
import { mkdtempSync, mkdirSync, readFileSync, rmSync, writeFileSync } from "node:fs"
import { tmpdir } from "node:os"
import { resolve } from "node:path"
import { activeRun, anchor, apply, blockDecision, memory, parsePromise, reviewOutcome, ruleFor, tickedItems, unearned } from "../watchdog/policy"

const parity = await Bun.file(resolve(import.meta.dir, "promise-parity.json")).json() as Array<Record<string, unknown>>
const canary = await Bun.file(resolve(import.meta.dir, "canary-false-blocks.json")).json() as Record<"runCardWrite" | "tickWrite", { command: string }>
const roots: string[] = []

function setup(ledger = '<li id="ISC-001"><input type="checkbox" disabled> open</li>') {
  const root = mkdtempSync(resolve(tmpdir(), "hive-policy-"))
  roots.push(root)
  mkdirSync(resolve(root, ".hivecall"))
  writeFileSync(resolve(root, ".hivecall/run.md"), "status: running\ngoal: Prove the policy\nledger: .hivecall/checklist.html\n\n## Owner rules\n- Never invent evidence\n")
  writeFileSync(resolve(root, ".hivecall/checklist.html"), ledger)
  return root
}

/** The tick-gate verdict on the ledger becoming `after`: "tick-gate" when a tick not already there is unearned, else null. */
function tickGate(after: string, state: ReturnType<typeof memory>, root: string) {
  const before = new Set(tickedItems(readFileSync(resolve(root, ".hivecall/checklist.html"), "utf8")))
  return unearned(after, state.approvals, before, root).length ? "tick-gate" : null
}

/** Runs a real shell command in `root` and returns the ledger it wrote, putting the old ledger back. */
function ledgerAfter(command: string, root: string) {
  const path = resolve(root, ".hivecall/checklist.html"), before = readFileSync(path, "utf8")
  Bun.spawnSync(["sh", "-c", command], { cwd: root })
  const after = readFileSync(path, "utf8")
  writeFileSync(path, before)
  return after
}

const revise = (state: ReturnType<typeof memory>, sessionID: string, slice: string) =>
  apply(state, { type: "review-result", sessionID, slice, approved: "", revised: 1 })

afterEach(() => { for (const root of roots.splice(0)) rmSync(root, { recursive: true, force: true }) })

function child(prompt = "TALK-BACK: report only BUG/BLOCKED/QUESTION/STOP.\nPROMISE: kind=helper rows=- result=- lane=-", extra = {}) {
  return { tool: "subagent", input: { agent: "build", description: "slice=ISC-001 build", prompt, ...extra }, sessionID: "ses-root" }
}

describe("Hivecall rule fixtures", () => {
  test("skill-gate blocks until delegation skill was loaded", () => {
    const state = memory()
    expect(ruleFor(child(), state, setup())?.id).toBe("skill-gate")
    state.skills.add("ses-root")
    expect(ruleFor(child(), state, setup())).toBeNull()
  })

  test("brief-check rejects missing TALK-BACK or invalid PROMISE", () => {
    const state = memory(); state.skills.add("ses-root")
    expect(ruleFor(child("PROMISE: kind=helper rows=- result=- lane=-"), state, setup())?.id).toBe("brief-check")
    expect(ruleFor(child("TALK-BACK: report.\nPROMISE: kind=review rows=- result=- lane=-"), state, setup())?.id).toBe("brief-check")
    expect(ruleFor(child(), state, setup())).toBeNull()
    expect(ruleFor(child("The talk-back section is below.\nPROMISE: kind=helper rows=- result=- lane=-"), state, setup())).toBeNull()
  })

  test("no-resume rejects a completed helper id but permits a fresh child", () => {
    const state = memory(); state.skills.add("ses-root"); state.finished.add("ses-old")
    expect(ruleFor(child(undefined, { sessionID: "ses-old" }), state, setup())?.id).toBe("no-resume")
    expect(ruleFor(child(), state, setup())).toBeNull()
  })

  test("reanchor carries goal, open item and owner rule", () => {
    const root = setup()
    expect(activeRun(root)).toBe(true)
    expect(anchor(root)).toContain("Goal: Prove the policy")
    expect(anchor(root)).toContain("Open counted items: ISC-001")
    expect(anchor(root)).toContain("- Never invent evidence")
  })

  test("tick-gate requires approval, commit id and existing evidence", () => {
    const root = setup()
    const content = '<li id="ISC-001"><input type="checkbox" checked> passed</li>\n| ISC-001 | PASS | commit abcdef1 | evidence .hivecall/proof.txt |'
    writeFileSync(resolve(root, ".hivecall/proof.txt"), "proof")
    const state = memory()
    expect(tickGate(content, state, root)).toBe("tick-gate")
    state.approvals.add("ISC-001")
    expect(tickGate(content, state, root)).toBeNull()
    rmSync(resolve(root, ".hivecall/proof.txt"))
    expect(tickGate(content, state, root)).toBe("tick-gate")
  })

  test("verified approval applies to the exact id across overlapping sessions", () => {
    const root = setup()
    writeFileSync(resolve(root, ".hivecall/proof.txt"), "proof")
    const state = memory()
    apply(state, { type: "review-result", sessionID: "ses-review", helper: "h1", slice: "ISC-001", approved: "ISC-001", revised: 0 })
    expect(unearned('<li id="ISC-001"><input type="checkbox" checked> done</li>\n| ISC-001 | PASS | commit abcdef1 | evidence .hivecall/proof.txt |', state.approvals, new Set(), root)).toEqual([])
  })

  test("tick-gate requires approval and a receipt for every newly ticked item", () => {
    const root = setup('<li id="ISC-001"><input type="checkbox" disabled> open</li>\n<li id="ISC-002"><input type="checkbox" disabled> open</li>')
    writeFileSync(resolve(root, ".hivecall/proof-1.txt"), "proof")
    writeFileSync(resolve(root, ".hivecall/proof-2.txt"), "proof")
    const content = [
      '<li id="ISC-001"><input type="checkbox" checked> passed</li>',
      "| ISC-001 | PASS | commit abcdef1 | evidence .hivecall/proof-1.txt |",
      '<li id="ISC-002"><input type="checkbox" checked> passed</li>',
      "| ISC-002 | PASS | commit abcdef2 | evidence .hivecall/proof-2.txt |",
    ].join("\n")
    const state = memory()
    state.approvals.add("ISC-001")
    expect(tickGate(content, state, root)).toBe("tick-gate")
    state.approvals.add("ISC-002")
    rmSync(resolve(root, ".hivecall/proof-2.txt"))
    expect(tickGate(content, state, root)).toBe("tick-gate")
    writeFileSync(resolve(root, ".hivecall/proof-2.txt"), "proof")
    expect(tickGate(content, state, root)).toBeNull()
  })

  test("tick-gate approval is per exact ticked id, never from proposed text", () => {
    const root = setup('<li id="ISC-001"><input type="checkbox"> a</li>\n<li id="ISC-002"><input type="checkbox"> b</li>\n<li id="ISC-010"><input type="checkbox"> c</li>')
    writeFileSync(resolve(root, ".hivecall/proof.txt"), "proof")
    const row = (id: string) => `<li id="${id}"><input type="checkbox" checked> done</li>\n| ${id} | PASS | commit abcdef1 | evidence .hivecall/proof.txt |`
    const state = memory()
    apply(state, { type: "review-result", sessionID: "ses-root", helper: "h1", slice: "ISC-001", approved: "ISC-001", revised: 0 })
    // The slice= marker in the proposed text must not borrow ISC-001's approval for ISC-002.
    expect(tickGate(`slice=ISC-001\n${row("ISC-002")}`, state, root)).toBe("tick-gate")
    expect(tickGate(`<!-- ISC-001 -->\n${row("ISC-002")}`, state, root)).toBe("tick-gate")
    // One approval cannot cover a two-item write.
    expect(tickGate(`${row("ISC-001")}\n${row("ISC-002")}`, state, root)).toBe("tick-gate")
    expect(tickGate(row("ISC-001"), state, root)).toBeNull()
    // ISC-1 is ISC-001, never ISC-010; a receipt row is matched to its own first id.
    const short = memory()
    apply(short, { type: "review-result", sessionID: "ses-root", helper: "h2", slice: "ISC-1", approved: "ISC-1", revised: 0 })
    expect(tickGate(row("ISC-010"), short, root)).toBe("tick-gate")
    expect(tickGate(row("ISC-1").replace('id="ISC-1"', 'id="ISC-001"'), short, root)).toBeNull()
    apply(short, { type: "review-result", sessionID: "ses-root", helper: "h3", slice: "ISC-010", approved: "ISC-010", revised: 0 })
    expect(tickGate('<li id="ISC-010"><input type="checkbox" checked> done</li>\n| ISC-001 | PASS | commit abcdef1 | evidence .hivecall/proof.txt |', short, root)).toBe("tick-gate")
    // A receipt that merely mentions the id, or names a sub-item, is not that id's receipt.
    apply(short, { type: "review-result", sessionID: "ses-root", helper: "h4", slice: "ISC-002", approved: "ISC-002", revised: 0 })
    const both = '<li id="ISC-001"><input type="checkbox" checked> a</li>\n<li id="ISC-002"><input type="checkbox" checked> b</li>\n'
    expect(tickGate(`${both}| ISC-002 | PASS | commit abcdef1 | evidence .hivecall/proof.txt | after ISC-001 |`, short, root)).toBe("tick-gate")
    expect(tickGate('<li id="ISC-001"><input type="checkbox" checked> a</li>\n| ISC-1.2 | PASS | commit abcdef1 | evidence .hivecall/proof.txt |', short, root)).toBe("tick-gate")
  })

  test("tick-gate attributes each receipt on one ledger line to its own item", () => {
    const root = setup('<li id="ISC-001"><input type="checkbox"> a</li>\n<li id="ISC-002"><input type="checkbox"> b</li>')
    writeFileSync(resolve(root, ".hivecall/proof-1.txt"), "proof")
    writeFileSync(resolve(root, ".hivecall/proof-2.txt"), "proof")
    const after = (second: string) => '<li id="ISC-001"><input type="checkbox" checked> a</li><li id="ISC-002"><input type="checkbox" checked> b</li>\n' +
      `ISC-001 commit abcdef1 evidence .hivecall/proof-1.txt; ${second}`
    const state = memory()
    for (const id of ["ISC-001", "ISC-002"]) state.approvals.add(id)
    expect(tickGate(after("ISC-002 commit abcdef2 evidence .hivecall/proof-2.txt"), state, root)).toBeNull()
    expect(tickGate(after("ISC-002 done"), state, root)).toBe("tick-gate")
    expect(tickGate(after("ISC-002 commit abcdef2 evidence .hivecall/forged.txt"), state, root)).toBe("tick-gate")
    state.approvals.delete("ISC-002")
    expect(tickGate(after("ISC-002 commit abcdef2 evidence .hivecall/proof-2.txt"), state, root)).toBe("tick-gate")
  })

  test("review outcomes approve exact scoped ids and honour the overall decision", () => {
    expect(reviewOutcome("Decision: `APPROVE_CODE`", ["ISC-001", "ISC-002"])).toEqual({ approved: ["ISC-001", "ISC-002"], revised: false })
    expect(reviewOutcome("- Decision: `REVISE_CODE`\n- ISC-001 — `APPROVE_CODE`\n- ISC-002 — `REVISE_CODE`", ["ISC-001", "ISC-002"]))
      .toEqual({ approved: ["ISC-001"], revised: true })
    expect(reviewOutcome("Decision: REVISE_CODE. Earlier draft said APPROVE_CODE.", ["ISC-001"])).toEqual({ approved: [], revised: true })
    expect(reviewOutcome("ISC-002 APPROVE_CODE", ["ISC-001"])).toEqual({ approved: [], revised: false })
    expect(reviewOutcome("No verdict here", ["ISC-001"])).toBeNull()
    const state = memory()
    const event = { type: "review-result", sessionID: "s", helper: "thr_a", slice: "ISC-001", approved: "", revised: 1 }
    apply(state, event); apply(state, event)
    expect(state.revisions.get("s:ISC-001")).toBe(1) // the same helper result read twice counts once
  })

  test("no-early-done blocks a final report or a close with open work, allows a parked run and an earned close", () => {
    const root = setup()
    const call = { tool: "write", sessionID: "ses-root", input: { path: ".hivecall/run.md", content: "status: running\ngoal: x\n## Final report\nDone" } }
    expect(ruleFor(call, memory(), root)?.id).toBe("no-early-done")
    const closed = { ...call, input: { ...call.input, content: "status: closed\ngoal: x\n## Final report\nDone" } }
    expect(ruleFor(closed, memory(), root)?.detail).toBe("open: ISC-001")
    expect(ruleFor({ ...call, input: { ...call.input, content: "status: parked\ngoal: x\n## Final report\nDone" } }, memory(), root)).toBeNull()
    writeFileSync(resolve(root, ".hivecall/checklist.html"), '<li id="ISC-001"><input type="checkbox" checked> a</li>\n| ISC-001 | PASS | commit abcdef1 | evidence .hivecall/run.md |')
    expect(ruleFor(closed, memory(), root)?.detail).toBe("ticked without approval and receipt: ISC-001")
    const approved = memory()
    approved.approvals.add("ISC-001")
    expect(ruleFor(closed, approved, root)).toBeNull()
    writeFileSync(resolve(root, ".hivecall/checklist.html"), '<li id="ISC-001"><input type="checkbox" disabled> open</li>')
    const patch = { tool: "patch", sessionID: "ses-root", input: { patchText: "*** Begin Patch\n*** Update File: unrelated.txt\n@@\n+untouched\n*** Update File: .hivecall/run.md\n@@\n+## Final report\n+Done\n*** End Patch" } }
    const shell = { tool: "shell", sessionID: "ses-root", input: { command: `python3 -c "Path('.hivecall/run.md').write_text('status: running\\n## Final report')"` } }
    expect(ruleFor(patch, memory(), root)?.id).toBe("no-early-done")
    expect(ruleFor(shell, memory(), root)?.id).toBe("no-early-done")
  })

  test("a fresh run card from the kickoff template has no Final report heading and writing it is allowed (canary 18:08:38)", async () => {
    const root = setup()
    const kickoff = await Bun.file(resolve(import.meta.dir, "../references/kickoff.md")).text()
    const template = kickoff.match(/```markdown\n(# Hivecall run card\n[\s\S]*?)```/)![1]
    expect(template).not.toMatch(/Final report/i)
    const write = (content: string) => ({ tool: "write", sessionID: "ses-root", input: { path: ".hivecall/run.md", content } })
    expect(ruleFor(write(template), memory(), root)).toBeNull()
    // The canary's real heredoc, written from the new template (no trailing empty heading), is allowed.
    const fresh = canary.runCardWrite.command.replace("\n\n## Final report\nEOF", "\nEOF")
    expect(fresh).not.toMatch(/Final report/)
    expect(ruleFor({ tool: "shell", sessionID: "ses-root", input: { command: fresh } }, memory(), root)).toBeNull()
    // Adding the heading to that card while items are open still blocks.
    writeFileSync(resolve(root, ".hivecall/run.md"), template)
    const fill = { tool: "edit", sessionID: "ses-root", input: { path: ".hivecall/run.md", oldString: "## Lessons\n", newString: "## Lessons\n\n## Final report\nConfirmed 4/4\n" } }
    expect(ruleFor(fill, memory(), root)?.id).toBe("no-early-done")
  })

  test("no-early-done blocks any Final report heading while items are open, however it is wrapped", () => {
    const root = setup()
    const write = (content: string) => ({ tool: "write", sessionID: "ses-root", input: { path: ".hivecall/run.md", content } })
    for (const content of [
      "status: running\n<!-- <<END -->\n## Final report\nEND\nAll counted items are complete.\n",
      "status: running\n<!-- ## Final report -->\nAll counted items are complete.\n",
      "status: running\n<!--\n## Final report\nAll counted items are complete.\n-->\n",
      "status: running\n## Final report\n### Summary\nAll counted items are complete.\n",
    ]) expect(ruleFor(write(content), memory(), root)?.id).toBe("no-early-done")
  })

  test("a backtick-quoted evidence path must exist exactly; only unquoted prose drops trailing punctuation", () => {
    const root = setup()
    writeFileSync(resolve(root, ".hivecall/proof.md"), "proof")
    const state = memory()
    state.approvals.add("ISC-001")
    const tick = (receipt: string) => `<li id="ISC-001"><input type="checkbox" checked> ISC-001 commit abcdef1 ${receipt}</li>`
    expect(tickGate(tick("evidence `.hivecall/proof.md.`"), state, root)).toBe("tick-gate")
    expect(tickGate(tick("evidence `.hivecall/proof.md`"), state, root)).toBeNull()
    expect(tickGate(tick("evidence .hivecall/proof.md."), state, root)).toBeNull()
  })

  test("tick-gate reads an evidence path that ends at a closing tag (canary 18:16:44)", () => {
    const ledger = [1, 2, 3, 4].map((i) => `<li id="ISC-${i}"><input type="checkbox" disabled> ISC-${i}: item</li>`).join("\n") +
      '\n<section id="verification">\n<ul>\n</ul>\n</section>'
    const root = setup(ledger)
    mkdirSync(resolve(root, ".hivecall/verification"))
    writeFileSync(resolve(root, ".hivecall/verification/qa-s1-670e8ee.md"), "PASS")
    const state = memory()
    for (const id of ["ISC-001", "ISC-002", "ISC-003", "ISC-004"]) state.approvals.add(id)
    expect(tickGate(ledgerAfter(canary.tickWrite.command, root), state, root)).toBeNull()
    // A genuinely missing evidence file still blocks in the same shape.
    expect(tickGate(ledgerAfter(canary.tickWrite.command.replaceAll("qa-s1-670e8ee.md</li>", "qa-s1-missing.md</li>"), root), state, root)).toBe("tick-gate")
  })

  test("an item id inside an evidence path belongs to that receipt (canary 2: verification/isc-1.log)", () => {
    const root = setup('<li id="ISC-1"><input type="checkbox" disabled> a</li>\n<li id="ISC-2"><input type="checkbox" disabled> b</li>')
    mkdirSync(resolve(root, ".hivecall/verification"))
    writeFileSync(resolve(root, ".hivecall/verification/isc-1.log"), "PASS")
    const state = memory()
    for (const id of ["ISC-001", "ISC-002"]) state.approvals.add(id)
    const after = (evidence: string) => '<li id="ISC-1"><input type="checkbox" disabled checked> a</li>\n<li id="ISC-2"><input type="checkbox" disabled checked> b</li>\n' +
      `<li>ISC-1: PASS - ok; evidence .hivecall/verification/isc-1.log; commit 0ff905f</li>\n<li>ISC-2: PASS - ok; evidence ${evidence}; commit 0ff905f</li>`
    expect(tickGate(after(".hivecall/verification/isc-1.log"), state, root)).toBeNull()
    expect(tickGate(after(".hivecall/verification/isc-2.log"), state, root)).toBe("tick-gate")
  })

  test("third-fix blocks the third fix on a slice and allows another slice", () => {
    const state = memory(); state.skills.add("ses-root")
    revise(state, "ses-root", "ISC-001")
    revise(state, "ses-root", "ISC-001")
    expect(ruleFor(child(), state, setup())?.id).toBe("third-fix")
    expect(ruleFor(child("TALK-BACK: report.\nPROMISE: kind=helper rows=- result=- lane=-", { description: "slice=ISC-002 build" }), state, setup())).toBeNull()
  })

  test("third-fix applies to implementation fixes, not review or research assignments", () => {
    const state = memory(); state.skills.add("ses-root")
    revise(state, "ses-root", "ISC-001")
    revise(state, "ses-root", "ISC-001")
    const root = setup()
    expect(ruleFor(child(undefined, { agent: "build" }), state, root)?.id).toBe("third-fix")
    expect(ruleFor(child(undefined, { agent: "general", description: "slice=ISC-001 fix implementation" }), state, root)?.id).toBe("third-fix")
    for (const agent of ["reviewer", "qa", "research"])
      expect(ruleFor(child(undefined, { agent }), state, root)).toBeNull()
    expect(ruleFor(child(undefined, { agent: "general", description: "slice=ISC-001 research options" }), state, root)).toBeNull()
  })

  test("each promise parity fixture matches the Python contract", () => {
    for (const row of parity) {
      const parsed = parsePromise(String(row.text))
      expect(parsed?.valid ?? null).toBe(row.valid)
      if (parsed) {
        expect(parsed.kind).toBe(row.kind)
        expect([...parsed.rows].sort()).toEqual(row.rows)
        expect(parsed.pace).toBe(row.pace)
      }
    }
  })

  test("rule list drift is rejected, including a deliberate unknown id", async () => {
    const skill = await Bun.file(resolve(import.meta.dir, "../SKILL.md")).text()
    const rules = await Bun.file(resolve(import.meta.dir, "../rules.json")).json() as Array<{ id: string }>
    const check = (source: string) => {
      const statement = source.match(/enforces ([^.]+)\./)?.[1] ?? ""
      const ids = [...statement.matchAll(/`([^`]+)`/g)].map((match) => match[1]).sort()
      const expected = rules.map((rule) => rule.id).sort()
      return JSON.stringify(ids) === JSON.stringify(expected)
    }
    expect(check(skill)).toBe(true)
    expect(check(skill.replace("`third-fix`", "`third-fix`, `orphan-rule`"))).toBe(false)
  })

  test("the neutral policy core names no BB command", async () => {
    const source = await Bun.file(resolve(import.meta.dir, "../watchdog/policy.ts")).text()
    expect(source.match(/\bbb\b|stampAgent/gi)).toBeNull()
  })

  test("the fourth block is allowed after a three-block cap", () => {
    const state = memory()
    expect([blockDecision(state, "ses-root", "brief-check").block,
      blockDecision(state, "ses-root", "brief-check").block,
      blockDecision(state, "ses-root", "brief-check").block]).toEqual([true, true, true])
    expect(blockDecision(state, "ses-root", "brief-check")).toEqual({ block: false, count: 3, warn: true })
  })
})
