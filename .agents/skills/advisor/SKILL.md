---
name: advisor
description: Ask five independent models, each in its own visible BB child thread, to critique a problem or propose a shape, then synthesize where they agree, disagree, and add unique angles. Use when the user says "advisor", asks for independent advisors or a multi-model panel inside BB, or wants a neutral critique of a problem statement or a high-level shape to build from. For a quick opinion without BB threads, use second-opinion; for an ISA-backed behavior contract, use shape-with-council.
---

# Advisor

Five advisors answer the same neutral brief, separately. You compare them. The value comes from independence, so protect it.

## Pick the playbook

| The user brings | Playbook | You return |
|---|---|---|
| A problem statement, or "does X solve this?" | [references/critique.md](references/critique.md) | Synthesis: agreements, disagreements, unique angles, next-step options |
| An idea or problem to build toward | [references/shape.md](references/shape.md) | A short spec the main agent implements from |

## Workflow

1. **Write a neutral, non-biased brief with no leading details.** Follow the playbook's template and the neutrality rule below. Save it to a temp file.
2. **Neutrality check.** Before sending, reread the brief against the checklist below. Fix any hit. Show the user the brief when the stakes are high or they asked to see it.
3. **Launch five advisors** as visible BB child threads of the current thread, one per model, same brief. An odd number avoids ties:

   ```bash
   bb thread spawn --parent-thread <this-thread-id> --project <project-id> \
     --environment <this-environment-id> --provider opencode \
     --model <model> --reasoning-level <level> --visibility visible \
     --title "Advisor (<name>): <short topic>" --prompt "$(cat <brief-file>)"
   ```

   Resolve ids with `bb thread show --self --json`; if that fails, find the current thread per the BB delegation rules. Never omit the parent. Default models and levels, unless the user names others: `openai/gpt-6.1-sol` high, `anthropic/claude-opus-5-5` high, `anthropic/claude-sonnet-5-5` high, `ollama-cloud/deepseek-v4.1-flash:1017` high, `anthropic/claude-fable-5-1` low. Check `bb provider models opencode` if one is missing.
4. **Do not wait or poll.** Tell the user the five threads started and end the turn. Continue when completion notices arrive. Read full answers with `bb thread output <id>`.
5. **Synthesize yourself** per the playbook. Advisors return raw answers only; you, the parent agent, compare them. Attribute views to models only in the synthesis, never in a later brief.

## Neutral brief checklist

**Rule: the brief must be neutral, non-biased, and free of leading details.** It gives the problem, hard limits, facts, and the question. It never hints at an answer. If a line could steer an advisor, cut it. A leading brief makes agreement worthless.

- No recommendation, no "my pick", no ranking of options.
- If options are listed, each gets its strongest case and its costs, in the same depth.
- No reasoning that pre-decides the answer. Do not point out the flaw or insight you expect advisors to find.
- Owner premises hold only hard limits, such as privacy, cost, and who merges; label them "owner premise". Never a design choice, a prior round's conclusion, or the user's opinion of an option.
- When in doubt, send only the problem, hard limits, and facts.
- Disagreements from earlier rounds appear only as open questions, never as someone's answer.
- Asks every advisor for one unique angle the others would likely miss.

## Advisor rules (put in every brief)

- Role: terminal worker, read-only. Do not edit files, run writing commands, spawn threads or subagents, or ask other models.
- May read the repo and search the web; cite external sources as URLs.
- Be adversarial, concise, and answer in the playbook's numbered order.
- Return only your own raw answer. Do not synthesize, compare, or merge with other advisors.
