import { afterEach, describe, expect, test } from "bun:test"
import { execSync } from "node:child_process"
import { appendFileSync, writeFileSync } from "node:fs"
import { resolve } from "node:path"
import { cleanups, host } from "./host"

// Hill climb and Reflect, then adapt (HOW-TO-WORK.md rules 7 and 10), and the judge stays apart (rule 2).
afterEach(() => { for (const cleanup of cleanups.splice(0)) cleanup() })

type Host = Awaited<ReturnType<typeof host>>
const brief = (rows: string, extra = "") => `PROMISE: kind=helper rows=${rows} result=- lane=-\nTALK-BACK: report BUG only.\n${extra}`
let n = 0
async function review(h: Host, verdict: string, slice: string, extra = "") {
  const id = `rev${++n}`
  expect(await h.helper({ id, agent: "reviewer", prompt: `slice=${slice}\n${brief("ISC-001", extra)}`, verdicts: `ISC-001 ${verdict}` })).toContain("Recorded")
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

  test("a new run starts with no failed attempts from the last one", async () => {
    const h = await host({ card: true })
    await h.call("skill", { id: "subagent-delegation" })
    for (const slice of ["v1", "v2", "v3"]) await review(h, "REVISE_CODE", slice)
    expect(await build(h)).toContain("RE-PLAN item=ISC-001")
    writeFileSync(resolve(h.root, ".hivecall/run.md"), "status: done\n")
    await h.call("skill", { id: "hivecall" })
    writeFileSync(resolve(h.root, ".hivecall/run.md"), "status: running\ngoal: g2\nledger: .hivecall/checklist.html\n")
    expect(await build(h)).toBeNull()
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
    // An older canary does not cover a later commit that bends the check again.
    writeFileSync(resolve(h.root, "check.ts"), "exit(0) // again\n")
    git("commit -qam bend2")
    const next = git("rev-parse --short HEAD")
    const old = `<li>ISC-001: PASS; commit ${sha}; evidence .hivecall/proof.txt; CANARY: broken page exits 1</li>`
    expect(await h.call("write", { path: ".hivecall/checklist.html", content: `${ledger("")}\n${old}\n<li>ISC-001: PASS; commit ${next}; evidence .hivecall/proof.txt</li>` })).toContain("CANARY")
  })

  const qa = async (h: Host, sha: string, verdict: string) => {
    const id = `qa${++n}`
    expect(await h.helper({ id, agent: "qa", prompt: brief("ISC-001", `candidate ${sha}\nWHY: re-test after the ledger changed`), verdicts: `ISC-001 ${verdict}` })).toContain("Recorded")
  }
  const testOnly = async () => {
    const { h, git } = await repo()
    const base = git("rev-parse --short HEAD")
    execSync("mkdir -p tests", { cwd: h.root })
    writeFileSync(resolve(h.root, "tests/a.test.ts"), "test()\n")
    git("add -A"); git("commit -qm tests")
    return { h, base, sha: git("rev-parse --short HEAD") }
  }
  const tick = (sha: string, parentRow: string) => `<li id="ISC-001"><input type="checkbox" checked> a</li>\n<li>ISC-001: PASS; commit ${sha}; evidence .hivecall/proof.txt</li>\n${parentRow}`

  test("a tests-only commit on a proven parent ticks on qa PASS alone, not on a repro or a failed parent", async () => {
    const failRow = (base: string) => `<li id="ISC-002"><input type="checkbox"> b</li>\n| ISC-002 | FAIL | commit ${base} |`
    const prove = (h: Host, base: string) => appendFileSync(resolve(h.root, ".hivecall/run.md"), `base: ${base}\n`)
    let { h, base, sha } = await testOnly()
    await qa(h, sha, "PASS")
    // A parent named only by a FAIL row is not proven.
    expect(await h.call("write", { path: ".hivecall/checklist.html", content: tick(sha, failRow(base)) })).toContain("ISC-001")
    prove(h, base)
    expect(await h.call("write", { path: ".hivecall/checklist.html", content: tick(sha, failRow(base)) })).toBeNull()
    ;({ h, base, sha } = await testOnly())
    prove(h, base)
    await qa(h, sha, "REPRODUCED")
    expect(await h.call("write", { path: ".hivecall/checklist.html", content: tick(sha, failRow(base)) })).toContain("ISC-001")
    // A PASS on another commit does not cover this one, and a later FAIL cancels a PASS.
    ;({ h, base, sha } = await testOnly())
    prove(h, base)
    await qa(h, base, "PASS")
    expect(await h.call("write", { path: ".hivecall/checklist.html", content: tick(sha, failRow(base)) })).toContain("ISC-001")
    ;({ h, base, sha } = await testOnly())
    prove(h, base)
    await qa(h, sha, "PASS")
    await qa(h, sha, "FAIL")
    expect(await h.call("write", { path: ".hivecall/checklist.html", content: tick(sha, failRow(base)) })).toContain("ISC-001")
  })

  test("a .txt change still needs a code review", async () => {
    const { h, git } = await repo()
    const base = git("rev-parse --short HEAD")
    appendFileSync(resolve(h.root, ".hivecall/run.md"), `base: ${base}\n`)
    writeFileSync(resolve(h.root, "requirements.txt"), "left-pad==2\n")
    git("add -A"); git("commit -qm deps")
    const sha = git("rev-parse --short HEAD")
    await qa(h, sha, "PASS")
    expect(await h.call("write", { path: ".hivecall/checklist.html", content: tick(sha, "") })).toContain("ISC-001")
  })

  test("a qa FAIL verdict counts toward the hill-climb pause", async () => {
    const { h, git } = await repo()
    const sha = git("rev-parse --short HEAD")
    for (let i = 0; i < 3; i++) await qa(h, sha, "FAIL")
    expect(await build(h)).toContain("RE-PLAN item=ISC-001")
  })
})
