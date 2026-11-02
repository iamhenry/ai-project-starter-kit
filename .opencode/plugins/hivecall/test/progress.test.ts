import { afterEach, describe, expect, test } from "bun:test"
import { execSync } from "node:child_process"
import { writeFileSync } from "node:fs"
import { resolve } from "node:path"
import { cleanups, host } from "./host"

// Hill climb and Reflect, then adapt (HOW-TO-WORK.md rules 7 and 10), and the judge stays apart (rule 2).
afterEach(() => { for (const cleanup of cleanups.splice(0)) cleanup() })

type Host = Awaited<ReturnType<typeof host>>
const brief = (rows: string, extra = "") => `PROMISE: kind=helper rows=${rows} result=- lane=-\nTALK-BACK: report BUG only.\n${extra}`
let n = 0
async function review(h: Host, verdict: string, slice: string, extra = "") {
  const id = `rev${++n}`
  expect(h.before({ sessionID: "ses-root", id, tool: "subagent", input: { agent: "reviewer", description: `slice=${slice}`, prompt: brief("ISC-001", extra) } })).toBeUndefined()
  await h.send("session.tool.success", { sessionID: "ses-root", id, metadata: { sessionID: `ses_${id}`, status: "completed" },
    content: [{ type: "text", text: `- Decision: \`${verdict}\`` }] })
}
const build = (h: Host, extra = "") => h.call("subagent", { agent: "build", description: "slice=next", prompt: brief("ISC-001", extra) })
const replan = (next: string) => `RE-PLAN item=ISC-001\nTried: three fixes to the outline walker\nEvidence: .hivecall/proof.txt\nNext: ${next}`

describe("hill climb", () => {
  test("a normal build, review and qa round never pauses", async () => {
    const h = await host({ card: true })
    await h.call("skill", { id: "subagent-delegation" })
    await review(h, "REVISE_CODE", "a")
    await review(h, "APPROVE_CODE", "a")
    expect(await h.call("subagent", { agent: "qa", description: "qa", prompt: brief("ISC-001", "WHY: no repo here") })).toBeNull()
  })

  test("three failed attempts pause the item until a RE-PLAN reflects on them", async () => {
    const h = await host({ card: true })
    await h.call("skill", { id: "subagent-delegation" })
    // Renaming the slice each time escapes third-fix; the per-item count still sees three failed attempts.
    for (const slice of ["v1", "v2", "v3"]) await review(h, "REVISE_CODE", slice)
    expect(await build(h)).toContain("RE-PLAN item=ISC-001")
    expect(await build(h, replan("polish the check again"))).toContain("must start with new angle, split or park")
    expect(await build(h, replan("new angle: build the outline from the DOM instead"))).toBeNull()
    expect(h.events().some((row) => row.type === "replan" && row.item === "ISC-001")).toBe(true)
    // Five failed attempts run-wide with no tick also need a run-level RE-PLAN.
    const run = (next: string) => `RE-PLAN item=run\nTried: six reviews on one item\nEvidence: .hivecall/proof.txt\nNext: ${next}`
    await review(h, "REVISE_CODE", "v4")
    await review(h, "REVISE_CODE", "v5")
    expect(() => h.before({ sessionID: "ses-root", id: "gated", tool: "subagent", input: { agent: "reviewer", description: "slice=v6", prompt: brief("ISC-001") } })).toThrow("item=run")
    await review(h, "REVISE_CODE", "v6", run("split the walker from the check"))
    expect(await build(h, replan("new angle: build the outline from the DOM instead"))).toContain("repeats the previous RE-PLAN")
    expect(await build(h, replan("park until the owner picks the reference page"))).toBeNull()
  })
})

describe("the judge stays apart", () => {
  const repo = async () => {
    const h = await host({ card: true })
    const git = (cmd: string) => execSync(`git -c user.email=t@t -c user.name=t ${cmd}`, { cwd: h.root, encoding: "utf8" }).trim()
    git("init -q")
    writeFileSync(resolve(h.root, ".gitignore"), ".hivecall/\n")
    writeFileSync(resolve(h.root, "check.ts"), "exit(1)\n")
    git("add -A"); git("commit -qm base")
    await h.call("skill", { id: "subagent-delegation" })
    return { h, git }
  }

  test("qa names an existing commit, and a passed item with no change is not re-checked", async () => {
    const { h, git } = await repo()
    const sha = git("rev-parse --short HEAD")
    expect(await h.call("subagent", { agent: "qa", description: "qa", prompt: brief("ISC-001") })).toContain("names no commit")
    expect(await h.call("subagent", { agent: "qa", description: "qa", prompt: brief("ISC-001", `candidate ${sha}`) })).toBeNull()
    writeFileSync(resolve(h.root, ".hivecall/checklist.html"),
      `<li id="ISC-001"><input type="checkbox" checked> a</li>\n<li>ISC-001: PASS; commit ${sha}; evidence .hivecall/proof.txt</li>`)
    expect(await h.call("subagent", { agent: "qa", description: "qa", prompt: brief("ISC-001", `candidate ${sha}`) })).toContain("already passed")
    expect(await h.call("subagent", { agent: "qa", description: "qa", prompt: brief("ISC-001", `candidate ${sha}\nWHY: the merge changed the reader`) }) ?? "").not.toContain("Work off deltas")
  })

  test("a tick whose commit edits its own check needs a CANARY line", async () => {
    const { h, git } = await repo()
    writeFileSync(resolve(h.root, "check.ts"), "exit(0)\n")
    git("commit -qam bend")
    const sha = git("rev-parse --short HEAD")
    await review(h, "APPROVE_CODE", "a")
    const ledger = (extra: string) => `<li id="ISC-001"><input type="checkbox" checked> a — check: bun check.ts</li>\n<li>ISC-001: PASS; commit ${sha}; evidence .hivecall/proof.txt${extra}</li>`
    expect(await h.call("write", { path: ".hivecall/checklist.html", content: ledger("") })).toContain("CANARY")
    expect(await h.call("write", { path: ".hivecall/checklist.html", content: ledger("; CANARY: saved broken page still exits 1") })).toBeNull()
  })
})
