/**
 * Run-card model policy (HOW-TO-WORK.md rule 20: helpers run on the run's chosen models, never a hand-picked one).
 * `models: code -> provider/model#variant, qa -> …` names each agent's model; `backup models:` the ones allowed on a
 * usage-limit cutoff. An agent list `code/qa -> …` shares one model. Values that are not `provider/model` are ignored.
 */
export type ModelPolicy = { primary: Map<string, string>; backup: Map<string, string[]> }

const modelRef = /^[\w.-]+\/[\w.:@-]+(?:#[\w-]+)?$/

function pairs(card: string, label: string): Array<[string, string]> {
  const line = card.match(new RegExp(`^\\s*(?:[-*]\\s*)?${label}\\s*:\\s*(.+)$`, "im"))?.[1] ?? ""
  return line.split(/[,;]\s*(?=[\w/.-]+\s*->)/).flatMap((part) => {
    const [agents, model] = part.split("->").map((value) => value?.trim().replace(/[`"']/g, "").split(/\s+/)[0] ?? "")
    return agents && model && modelRef.test(model) ? agents.split("/").map((agent) => [agent.toLowerCase(), model] as [string, string]) : []
  })
}

export function modelPolicy(card: string): ModelPolicy {
  const primary = new Map(pairs(card, "models"))
  const backup = new Map<string, string[]>()
  for (const [agent, model] of pairs(card, "backup models")) backup.set(agent, [...(backup.get(agent) ?? []), model])
  return { primary, backup }
}

/** Models an agent may run on: its primary and its backups. */
export function allowedModels(policy: ModelPolicy, agent: string): string[] {
  return [...new Set([policy.primary.get(agent), ...(policy.backup.get(agent) ?? [])].filter((model): model is string => Boolean(model)))]
}

/** A helper failure that reads as a usage, credit or rate limit. */
export function usageLimit(text: string): boolean {
  return /usage limit|rate.?limit|quota|out of credits?|insufficient (?:credit|balance|funds)|billing|\b429\b|too many requests|limit (?:reached|exceeded)/i.test(text)
}
