import { afterEach, describe, expect, test } from "bun:test"
import { mkdtempSync, mkdirSync, readFileSync, rmSync, writeFileSync } from "node:fs"
import { tmpdir } from "node:os"
import { resolve } from "node:path"
import { bbAgentStamp, bbNoticeEvents, bbOutputRead, bbPinEvent, bbReadEvent, bbSpawnEvent, shellDelegation } from "../watchdog/adapters"
import { apply, helperIdentity, memory, ruleFor, unearned, type HiveEvent } from "../watchdog/policy"

const prompt = "TALK-BACK: report BUG/BLOCKED/QUESTION only.\nPROMISE: kind=helper rows=- result=- lane=-"

describe("BB shell delegation adapter", () => {
  test("parses quoted spawn prompts and title", () => {
    const result = shellDelegation(`bb thread spawn --parent-self --title "Fix slice" --prompt '${prompt}'`)
    expect(result.call?.tool).toBe("subagent")
    expect(result.call?.input).toMatchObject({ description: "Fix slice", prompt })
  })

  test("parses escaped double-quoted prompts", () => {
    const result = shellDelegation(`bb thread spawn --title review --prompt "TALK-BACK: include \\\"details\\\".\nPROMISE: kind=helper rows=- result=- lane=-"`)
    expect(result.call?.input.prompt).toBe('TALK-BACK: include "details".\nPROMISE: kind=helper rows=- result=- lane=-')
  })

  test("parses a heredoc prompt", () => {
    const result = shellDelegation(`bb thread spawn --parent-self --title "Fix slice" --prompt "$(cat <<'BRIEF'\n${prompt}\nBRIEF\n)"`)
    expect(result.call?.input).toMatchObject({ description: "Fix slice", prompt: `${prompt}\n` })
    // A command after the spawn cannot change its brief, so the spawn stays gated.
    expect(shellDelegation(`bb thread spawn --title x --prompt "$(cat <<'BRIEF'\n${prompt}\nBRIEF\n)" --json | grep '"id"'`).call?.input.prompt).toBe(`${prompt}\n`)
  })

  test("parsed BB spawns use the same neutral delegation gates", () => {
    const call = shellDelegation(`bb thread spawn --title "Fix slice" --prompt '${prompt}'`).call!
    expect(ruleFor({ ...call, sessionID: "ses-root" }, memory(), ".")?.id).toBe("skill-gate")
  })

  test("maps a BB tell brief with its target, but leaves a worker report alone", () => {
    expect(shellDelegation(`bb thread tell thr_example --mode steer '${prompt}'`).call?.input).toMatchObject({ prompt, sessionID: "thr_example" })
    expect(shellDelegation(`bb thread tell --mode queue --model m1 thr_example '${prompt}'`).call?.input).toMatchObject({ prompt, sessionID: "thr_example" })
    expect(shellDelegation("bb thread tell thr_example 'QUESTION: need one detail'").call).toBeUndefined()
  })

  test("shell-built prompts, titles and messages fail open with a diagnostic", () => {
    for (const command of [
      'bb thread spawn --title x --prompt "$BRIEF"',
      "bb thread spawn --title x --prompt $BRIEF",
      'bb thread spawn --title x --prompt="${BRIEF}"',
      'bb thread spawn --title x --prompt "$(cat brief.md)"',
      "bb thread spawn --title x --prompt \"`cat brief.md`\"",
      'bb thread spawn --title "$TITLE" --prompt \'' + prompt + "'",
      `bb thread spawn --title x --prompt "$(cat <<BRIEF\n${prompt}\nslice=$SLICE\nBRIEF\n)"`,
      "bb thread spawn --title x --prompt-file - ",
      'bb thread tell thr_example "$MSG"',
      "bb thread tell thr_example --message-file brief.md",
      'bb thread tell "$TID" \'' + prompt + "'",
    ]) {
      const result = shellDelegation(command)
      expect([command, result.call]).toEqual([command, undefined])
      expect(result.warning).toBeTruthy()
    }
    // Quoting that stops expansion is still a literal brief, so it stays gated.
    expect(shellDelegation(`bb thread spawn --title x --prompt '$BRIEF ${prompt}'`).call?.input.prompt).toBe(`$BRIEF ${prompt}`)
    expect(shellDelegation(`bb thread spawn --title x --prompt "\\$5 ${prompt}"`).call?.input.prompt).toBe(`$5 ${prompt}`)
    expect(shellDelegation(`bb thread spawn --title x --prompt "$(cat <<'BRIEF'\n$HOME ${prompt}\nBRIEF\n)"`).call?.input.prompt).toBe(`$HOME ${prompt}\n`)
  })

  test("file and heredoc briefs are gated on the text the helper gets", () => {
    const dir = mkdtempSync(resolve(tmpdir(), "hive-brief-"))
    try {
      writeFileSync(resolve(dir, "brief.md"), prompt)
      // The file as it is at hook time, with a command after the spawn.
      expect(shellDelegation("bb thread spawn --title x --prompt-file brief.md --json | python3 -c 'print(1)'", dir).call?.input.prompt).toBe(prompt)
      // The live-run shape: one command writes the brief with a heredoc, then spawns from it.
      const written = `mkdir -p .lanes && cat > .lanes/b.md <<'EOF'\nagent: reviewer\n${prompt}\nEOF\nbb thread spawn --title x --prompt-file .lanes/b.md --json | grep '"id"'`
      expect(shellDelegation(written, dir).call?.input).toMatchObject({ agent: "reviewer", prompt: `agent: reviewer\n${prompt}\n` })
      expect(shellDelegation(`bb thread spawn --title x --prompt-file - <<'EOF'\n${prompt}\nEOF`, dir).call?.input.prompt).toBe(`${prompt}\n`)
      expect(shellDelegation(`bb thread stop thr_old >/dev/null 2>&1; bb thread spawn --title x --prompt '${prompt}'`, dir).call?.input.prompt).toBe(prompt)
      // A missing TALK-BACK in the file still fails the neutral brief check.
      writeFileSync(resolve(dir, "bad.md"), "PROMISE: kind=helper rows=- result=- lane=-")
      const state = memory(); state.skills.add("ses-root")
      expect(ruleFor({ ...shellDelegation("bb thread spawn --prompt-file bad.md", dir).call!, sessionID: "ses-root" }, state, dir)?.id).toBe("brief-check")
      // What the hook cannot read exactly fails open with a warning, but is still a spawn.
      for (const command of ["bb thread spawn --prompt-file missing.md", "printf x > brief.md && bb thread spawn --prompt-file brief.md",
        "cd sub && bb thread spawn --prompt-file brief.md", `cat > b.md <<EOF\n$X ${prompt}\nEOF\nbb thread spawn --prompt-file b.md`,
        "printf x | bb thread spawn --prompt-file -"]) {
        const result = shellDelegation(command, dir)
        expect([command, result.call, result.kind, Boolean(result.warning)]).toEqual([command, undefined, "spawn", true])
      }
      expect(shellDelegation(`bb thread spawn --prompt '${prompt}'; bb thread spawn --prompt '${prompt}'`, dir).warning).toContain("Several")
    } finally { rmSync(dir, { recursive: true, force: true }) }
  })

  test("only a small regular brief file, or one unambiguous heredoc write before the spawn, is gated", () => {
    const dir = mkdtempSync(resolve(tmpdir(), "hive-brief-"))
    try {
      // A FIFO would hang a plain read and a huge file would flood memory: both fail open, as do stamp inputs.
      Bun.spawnSync(["mkfifo", resolve(dir, "fifo.md")])
      writeFileSync(resolve(dir, "big.md"), "a".repeat(300 * 1024))
      for (const name of ["fifo.md", "big.md"]) {
        const result = shellDelegation(`bb thread spawn --prompt-file ${name}`, dir)
        expect([name, result.call, Boolean(result.warning)]).toEqual([name, undefined, true])
      }
      expect(bbAgentStamp("bb plugin rpc call --input-file fifo.md opencode stampAgent").stamp).toBeUndefined()
      const write = (body: string) => `cat > b.md <<'EOF'\n${body}\nEOF\n`
      // The file the helper gets is not the heredoc text: changed again before the spawn, or only written after it.
      for (const command of [`${write(prompt)}printf bad > b.md\nbb thread spawn --prompt-file b.md`,
        `${write(prompt)}cat >> b.md <<'EOF'\nmore\nEOF\nbb thread spawn --prompt-file b.md`,
        `${write(prompt)}${write("no talk-back")}bb thread spawn --prompt-file b.md`,
        `bb thread spawn --prompt-file b.md\n${write(prompt)}`]) {
        const result = shellDelegation(command, dir)
        expect([command, result.call, result.kind, Boolean(result.warning)]).toEqual([command, undefined, "spawn", true])
      }
      // A rewrite after the spawn cannot change what it already sent.
      expect(shellDelegation(`${write(prompt)}bb thread spawn --prompt-file b.md; ${write("x")}`, dir).call?.input.prompt).toBe(`${prompt}\n`)
    } finally { rmSync(dir, { recursive: true, force: true }) }
  })

  test("a pin is only an executed stampAgent call, never stamp text in quotes, comments, heredocs or printf/echo", () => {
    const json = '{"threadId":"thr_a1","agent":"reviewer","queued":false}'
    const rpc = "bb plugin rpc call --input-file /dev/stdin opencode stampAgent"
    for (const command of [`printf '%s' '${json}' | ${rpc}`, `echo '${json}' | ${rpc} --json`, `${rpc} <<'EOF'\n${json}\nEOF`, `cat <<'EOF' | ${rpc}\n${json}\nEOF`])
      expect([command, bbAgentStamp(command).stamp]).toEqual([command, { thread: "thr_a1", agent: "reviewer" }])
    expect(bbAgentStamp(`printf '%s' '{"projectId":"proj_x","agent":"QA","queued":false}' | ${rpc}`).stamp).toEqual({ project: "proj_x", agent: "qa" })
    for (const command of [
      `printf '${rpc} ${json}'`, `echo "${rpc} '${json}'"`, `printf '%s\\n' '${rpc}' '${json}'`, `echo '${json}' # | ${rpc}`,
      `# printf '%s' '${json}' | ${rpc}`, `cat <<'EOF'\nprintf '%s' '${json}' | ${rpc}\nEOF`, `true || printf '%s' '${json}' | ${rpc}`,
      `printf '%s' '${json}' | ${rpc}; echo '{"ok":true}'`, `printf '%s' '${json}' | ${rpc} && true`, `echo hi\nprintf '%s' '${json}' | ${rpc}`,
      `printf '%s' "$PIN" | ${rpc}`, `printf '%s' '${json}' | ./bb plugin rpc call --input-file /dev/stdin opencode stampAgent`,
      `bb plugin rpc call --input-file pin.json opencode stampAgent`, `printf '%s' '{"projectId":null,"agent":"reviewer","queued":false}' | ${rpc}`]) {
      const result = bbAgentStamp(command)
      expect([command, result.stamp, Boolean(result.warning)]).toEqual([command, undefined, true])
    }
    expect(bbAgentStamp(`echo '${json}'`).stamp).toBeUndefined()
    expect(bbAgentStamp("bb thread list")).toEqual({})
  })

  test("a thread pin is verified only for a seen helper briefed with that role, after a successful RPC", () => {
    const state = memory()
    const identity = helperIdentity({ agent: "general", description: "r", prompt: "agent: reviewer\nTALK-BACK" })
    apply(state, bbSpawnEvent("ses-root", identity, "Thread spawned: thr_seen\n")!)
    const pin = (thread: string, agent: string, output = '{\n  "ok": true\n}\n', session = "ses-root") => bbPinEvent(state, session, { thread, agent }, output)
    expect(pin("thr_seen", "reviewer")).toEqual({ type: "helper-agent", sessionID: "thr_seen", parentSessionID: "ses-root", agent: "reviewer" })
    for (const output of ["Error: invalid_input: HTTP 400: rpc input validation failed", '{"ok":false}', "", '{"ok":true}\n{"ok":true}'])
      expect([output, pin("thr_seen", "reviewer", output)]).toEqual([output, null])
    expect(pin("thr_unseen", "reviewer")).toBeNull()
    expect(pin("thr_seen", "build")).toBeNull()
    expect(pin("thr_seen", "reviewer", '{"ok":true}', "ses-other")).toBeNull()
  })

  test("unparseable BB command fails open with a diagnostic", () => {
    expect(shellDelegation("printf x && bb thread spawn --prompt-file brief.txt").warning).toBeTruthy()
    expect(shellDelegation("bb thread spawn --prompt-file brief.txt").warning).toBeTruthy()
  })
})

describe("BB child-thread lifecycle feeds the neutral helper state", () => {
  const roots: string[] = []
  afterEach(() => { for (const root of roots.splice(0)) rmSync(root, { recursive: true, force: true }) })
  const run = () => {
    const root = mkdtempSync(resolve(tmpdir(), "hive-bb-"))
    roots.push(root)
    mkdirSync(resolve(root, ".hivecall"))
    writeFileSync(resolve(root, ".hivecall/run.md"), "status: running\ngoal: g\nledger: .hivecall/checklist.html\n")
    writeFileSync(resolve(root, ".hivecall/checklist.html"), '<li id="ISC-001"><input type="checkbox"> a</li>\n<li id="ISC-002"><input type="checkbox"> b</li>')
    writeFileSync(resolve(root, ".hivecall/proof.txt"), "proof")
    const state = memory(); state.skills.add("ses-root")
    return { root, state }
  }
  const brief = (role: string, rows: string) => `agent: ${role}\nslice=ISC-001\nTALK-BACK: report BUG/BLOCKED/QUESTION only.\nPROMISE: kind=helper rows=${rows} result=- lane=-`
  // What the plugin does on a `bb thread spawn` shell call: gate it, read the new thread id from its output, then
  // (Route B) see the orchestrator pin the thread's agent with `stampAgent`, unless `pin` is false.
  const spawn = (state: ReturnType<typeof memory>, root: string, role: string, thread: string, rows = "ISC-001", pin = true) => {
    const call = shellDelegation(`bb thread spawn --parent-self --title "${role} slice" --prompt '${brief(role, rows)}'`).call!
    const blocked = ruleFor({ ...call, sessionID: "ses-root" }, state, root)
    if (!blocked) emit(state, bbSpawnEvent("ses-root", helperIdentity(call.input), `Thread spawned: ${thread}\n`))
    const stamp = bbAgentStamp(`printf '%s' '{"threadId":"${thread}","agent":"${role}","queued":false}' | bb plugin rpc call --input-file /dev/stdin opencode stampAgent`).stamp!
    if (!blocked && pin) emit(state, bbPinEvent(state, "ses-root", stamp, '{"ok":true}'))
    return blocked?.id ?? null
  }
  const emit = (state: ReturnType<typeof memory>, event: HiveEvent | null) => { if (event) apply(state, event) }
  const notice = (thread: string, output: string) => `[bb system]\n\n@thread:${thread} completed:\n\n${output}`
  // The tick-gate verdict on rewriting the ledger with one ticked, receipted item.
  const tickGate = (state: ReturnType<typeof memory>, root: string) => {
    return unearned('<li id="ISC-001"><input type="checkbox" checked> a</li>\n| ISC-001 | PASS | commit abcdef1 | evidence .hivecall/proof.txt |',
      state.approvals, new Set(), root).length ? "tick-gate" : null
  }

  test("an approval from a BB thread whose brief only says reviewer does not count; the pin tells how to fix it", () => {
    const { root, state } = run()
    expect(spawn(state, root, "reviewer", "thr_unpinned", "ISC-001", false)).toBeNull()
    for (const event of bbNoticeEvents(state, "ses-root", notice("thr_unpinned", "Decision: APPROVE_CODE"))) emit(state, event)
    expect(state.finished.has("thr_unpinned")).toBe(true)
    expect(tickGate(state, root)).toBe("tick-gate")
  })

  test("BB spawn pinned as reviewer, then an approving notice, allows the tick", () => {
    const { root, state } = run()
    expect(tickGate(state, root)).toBe("tick-gate")
    expect(spawn(state, root, "reviewer", "thr_rev1")).toBeNull()
    for (const event of bbNoticeEvents(state, "ses-root", notice("thr_rev1", "- Decision: `APPROVE_CODE`\n- 0 findings"))) emit(state, event)
    expect(state.finished.has("thr_rev1")).toBe(true)
    expect(tickGate(state, root)).toBeNull()
  })

  test("the pinned agent, not the brief text, decides whether a result is a reviewer approval", () => {
    const { root, state } = run()
    spawn(state, root, "reviewer", "thr_pinned")
    emit(state, { type: "helper-agent", sessionID: "thr_pinned", parentSessionID: "ses-root", agent: "build" })
    for (const event of bbNoticeEvents(state, "ses-root", notice("thr_pinned", "Decision: APPROVE_CODE"))) emit(state, event)
    expect(tickGate(state, root)).toBe("tick-gate")
  })

  test("a reviewer result read with `bb thread output --json` also counts, once", () => {
    const { root, state } = run()
    spawn(state, root, "reviewer", "thr_rev2")
    const read = bbOutputRead("bb thread output thr_rev2 --json")!
    emit(state, bbReadEvent(state, read, JSON.stringify({ output: "Decision: APPROVE_CODE" })))
    expect(tickGate(state, root)).toBeNull()
    expect(bbOutputRead("bb thread output thr_rev2 | tail -3")).toBeNull()
  })

  test("two BB REVISE_CODE results on a slice block a third BB implementation fix", () => {
    const { root, state } = run()
    for (const thread of ["thr_r1", "thr_r2"]) {
      expect(spawn(state, root, "build", `${thread}fix`)).toBeNull()
      spawn(state, root, "reviewer", thread)
      const text = `[bb system]\n\nChild thread updates:\n- @thread:${thread}fix completed.\n- @thread:${thread} completed:\n\nDecision: REVISE_CODE`
      for (const event of bbNoticeEvents(state, "ses-root", text)) emit(state, event)
      // Re-reading the same result does not count as another revision.
      emit(state, bbReadEvent(state, { thread, json: false }, "Decision: REVISE_CODE"))
    }
    expect(state.revisions.get("ses-root:ISC-001")).toBe(2)
    expect(spawn(state, root, "build", "thr_fix3")).toBe("third-fix")
    expect(spawn(state, root, "reviewer", "thr_r3")).toBeNull()
    expect(tickGate(state, root)).toBe("tick-gate")
  })

  test("a tell to a finished BB helper is blocked; a tell to a running helper is allowed", () => {
    const { root, state } = run()
    spawn(state, root, "build", "thr_done")
    spawn(state, root, "build", "thr_live")
    for (const event of bbNoticeEvents(state, "ses-root", notice("thr_done", "RESULT: done"))) emit(state, event)
    const tell = (thread: string) => ruleFor({ ...shellDelegation(`bb thread tell ${thread} '${prompt}'`).call!, sessionID: "ses-root" }, state, root)?.id ?? null
    expect(tell("thr_done")).toBe("no-resume")
    expect(tell("thr_live")).toBeNull()
    // Interrupted or failed threads are not finished helpers.
    for (const event of bbNoticeEvents(state, "ses-root", "[bb system]\n\n@thread:thr_live was interrupted.\n\nReview the thread before deciding next steps.")) emit(state, event)
    expect(tell("thr_live")).toBeNull()
  })
})
