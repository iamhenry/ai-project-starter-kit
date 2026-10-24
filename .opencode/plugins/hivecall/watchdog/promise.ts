/** PROMISE line and item-id parsing; the TypeScript side of the contract shared with `watch.py` (see `test/promise-parity.json`). */
export const promiseDefaults: Record<string, number> = { screen: 10, timed: 15, build: 10, code: 20, helper: 20 }

/** Canonical item id: `ISC-1`, `isc-001` and `001` all become `ISC-001`; `ISC-1` and `ISC-10` stay distinct. */
export function iscId(raw: string): string {
  const [whole, ...parts] = raw.replace(/^ISC-/i, "").split(".")
  return `ISC-${String(Number(whole)).padStart(3, "0")}${parts.length ? `.${parts.join(".")}` : ""}`
}

export function iscIds(text: string): string[] {
  return [...new Set((text.match(/\bISC-\d+(?:\.\d+)*\b/gi) ?? []).map(iscId))]
}

export function parsePromiseRows(value: string): Set<string> | null {
  if (value === "-") return new Set()
  const rows = new Set<string>()
  for (const raw of value.split(",")) {
    const item = raw.trim()
    const range = item.match(/^(?:ISC-)?(\d+)-(?:ISC-)?(\d+)$/i)
    if (range) {
      const first = Number(range[1]), last = Number(range[2])
      if (last < first || last - first > 999) return null
      for (let n = first; n <= last; n++) rows.add(`ISC-${String(n).padStart(3, "0")}`)
      continue
    }
    if (!/^(?:ISC-)?\d+(?:\.\d+)?$/i.test(item)) return null
    rows.add(iscId(item))
  }
  return rows
}

export function parsePromise(text: string) {
  for (const line of text.split(/\r?\n/)) {
    const match = line.match(/^\s*PROMISE:\s*(.*)$/i)
    if (!match) continue
    const body = match[1]
    const marks = [...body.matchAll(/\b(kind|rows|result|lane|pace)=/gi)]
    const fields: Record<string, string> = {}
    marks.forEach((mark, i) => {
      fields[mark[1].toLowerCase()] = body.slice(mark.index! + mark[0].length, marks[i + 1]?.index ?? body.length).trim()
    })
    const kind = (fields.kind ?? "").toLowerCase()
    const rows = parsePromiseRows(fields.rows ?? "")
    const pace = fields.pace === undefined ? promiseDefaults[kind] ?? 0 : Number(fields.pace)
    const valid = Object.hasOwn(promiseDefaults, kind) && rows !== null &&
      ["rows", "result", "lane"].every((key) => key in fields) && Number.isFinite(pace) && pace > 0
    return { kind, rows: rows ?? new Set<string>(), result: fields.result ?? "-", lane: fields.lane ?? "-", pace,
      valid, error: valid ? "" : "invalid PROMISE line" }
  }
  return null
}
