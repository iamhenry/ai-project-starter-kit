---
name: advisor
description: Ask three independent models, each in its own visible BB child thread, to critique a problem or propose a shape, then synthesize where they agree, disagree, and add unique angles. Use when the user says "advisor", asks for independent advisors or a multi-model panel inside BB, or wants a neutral critique of a problem statement or a high-level shape to build from. For a quick opinion without BB threads, use second-opinion; for an ISA-backed behavior contract, use shape-with-council.
---

# Advisor

Three advisors answer the same neutral brief, separately. You compare them. The value comes from independence, so protect it.

## Pick the playbook

| The user brings | Playbook | You return |
|---|---|---|
| A problem statement, or "does X solve this?" | [references/critique.md](references/critique.md) | Synthesis: agreements, disagreements, unique angles, next-step options |
| An idea or problem to build toward | [references/shape.md](references/shape.md) | A short spec the main agent implements from |

## Workflow

1. **Write the brief.** Follow the playbook's template. Keep it neutral (below). Save it to a temp file.
2. **Neutrality check.** Before sending, reread the brief against the checklist below. Fix any hit. Show the user the brief when the stakes are high or they asked to see it.
3. **Launch three advisors** as visible BB child threads of the current thread, one per model, same brief:

   ```bash
   bb thread spawn --parent-thread <this-thread-id> --project <project-id> \
     --environment <this-environment-id> --provider opencode \
     --model <model> --reasoning-level high --visibility visible \
     --title "Advisor (<name>): <short topic>" --prompt "$(cat <brief-file>)"
   ```

   Resolve ids with `bb thread show --self --json`; if that fails, find the current thread per the BB delegation rules. Never omit the parent. Default models, unless the user names others: `openai/gpt-6.1-sol`, `anthropic/claude-sonnet-5-5`, `ollama-cloud/glm-5.3`. Check `bb provider models opencode` if one is missing.
4. **Do not wait or poll.** Tell the user the three threads started and end the turn. Continue when completion notices arrive. Read full answers with `bb thread output <id>`.
5. **Synthesize yourself** per the playbook. Advisors return raw answers only; you, the parent agent, compare them. Attribute views to models only in the synthesis, never in a later brief.

## Neutral brief checklist

- States facts, the user's decisions, and the question. No recommendation, no "my pick", no ranking of options.
- If options are listed, each gets its strongest case and its costs, in the same depth.
- No reasoning that pre-decides the answer. The user's own premises are allowed; label them "owner premise".
- Disagreements from earlier rounds appear only as open questions, never as someone's answer.
- Asks every advisor for one unique angle the others would likely miss.

## Advisor rules (put in every brief)

- Role: terminal worker, read-only. Do not edit files, run writing commands, spawn threads or subagents, or ask other models.
- May read the repo and search the web; cite external sources as URLs.
- Be adversarial, concise, and answer in the playbook's numbered order.
- Return only your own raw answer. Do not synthesize, compare, or merge with other advisors.
