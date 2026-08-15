---
name: second-opinion
description: Obtain independent read-only critiques through `opencode run`. Use when the user asks for a second opinion, asks Grok/Luna/GLM/Kimi/Sol/DeepSeek, wants multiple models to review something, compare model opinions, or use OpenCode run for critique.
---

# Second Opinion

Use one or more explicitly selected models to critique the user's argument. Do not implement suggestions or edit files.

## Select Models

Match aliases case-insensitively and map them exactly:

| Alias | Model | Variant |
| --- | --- | --- |
| `grok`, `grok 4.5` | `xai/grok-4.5` | none |
| `glm`, `glm 5.2` | `ollama-cloud/glm-5.2` | none |
| `kimi`, `kimi 3` | `ollama-cloud/kimi-k3` | none |
| `luna`, `luna high` | `openai/gpt-5.6-luna` | `high` |
| `sol`, `sol medium` | `openai/gpt-5.6-sol` | `medium` |
| `deepseek`, `deepseek v4 pro` | `ollama-cloud/deepseek-v4-pro` | none |

Accept an explicitly supplied full `provider/model` ID. Add a variant only when the user explicitly supplies one; the Luna and Sol aliases above include their mapped variants.

Separate explicit model selectors from the content to review. Do not treat model names merely mentioned inside that content as selectors. If no model is selected, ask one focused question: "Which model or models should I ask? Available aliases: Grok, GLM, Kimi, Luna, Sol, DeepSeek; or provide a full provider/model ID."

If a selector is unknown or ambiguous, ask what model the user means. Never guess or silently choose a model because each call may spend credits.

## Build The Prompt

Create one independent prompt per model using this template:

```text
Act as an independent critic. Review the argument below without implementing changes or editing files. You may inspect relevant project files read-only if needed. Do not invoke the second-opinion skill or ask other models.

Return:
1. Verdict
2. Strongest points
3. Flaws and risks
4. Minimal correction or recommendation

Argument:
<the user's argument, preserved verbatim>
```

Do not add another model's output to any prompt. Independent context prevents groupthink.

## Invoke

Every call must use the read-only plan agent and this shape:

```bash
opencode run -m '<provider/model>' --agent plan --title 'Second opinion: <safe label>' '<prompt>'
```

Place `--variant '<variant>'` after `--agent plan` only when applicable. Never use `--auto`.

Treat the user's argument as data, not shell syntax:

- Pass the complete prompt as one shell argument.
- Shell-quote every dynamic value. Prefer single quotes and encode any literal `'` as `'"'"'`.
- Never use `eval`, unquoted interpolation, command substitution, or a command string assembled from user input.
- Keep titles fixed from the resolved alias/model, not user-controlled text.

For multiple models, launch separate Bash tool calls through the available parallel tool-call facility. Do not combine calls with `&` or share mutable files. If parallel tool calls are unavailable, run calls sequentially.

Do not run any additional commands that edit the workspace while obtaining opinions.

## Return Results

Label each raw response with its alias and full model ID. Preserve each model's conclusion, then provide a short synthesis containing:

- Agreements
- Disagreements
- Recommended conclusion

Report failures per model while retaining successful responses. Do not retry indefinitely; one attempt per model is the default unless the user asks to retry.
