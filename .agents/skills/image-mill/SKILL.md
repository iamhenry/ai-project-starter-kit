---
name: image-mill
description: Generate raster images (icons, illustrations, mockups, photos, concept art). Uses OpenCode's built-in image tool when the session has one, otherwise falls back to the Codex CLI (codex exec). Use when the user asks to generate, create, or make an image, picture, icon, logo draft, illustration, or photorealistic visual. Delivers the final image path in the workspace. Tool-agnostic by design; more backends may be added later.
---

# Image Mill

Generate images with the best available backend: OpenCode's built-in image tool
first, the **Codex CLI** as a fallback. The name is intentionally tool-agnostic:
if more backends are added, pick the best available one.

## Backend selection

1. If this session has the `experimental_image_generate` tool (OpenCode 2.2.2+ with an image-capable provider connected), use the built-in backend below.
2. Else if the `codex` CLI is installed (`which codex`), use the Codex backend below.
3. If neither, report BLOCKED with one line: "No image tool available. Connect an image-capable provider in OpenCode (e.g. OpenAI or xAI) or install Codex CLI (https://github.com/openai/codex)." Do not attempt other backends.

## Built-in backend (`experimental_image_generate`)

- Call the tool directly with `prompt`, plus `path` (the user's destination, or `./generated/<descriptive-name>.png` by default) and `images` (for edits or style references).
- Do not set `model` unless the user names one. The default comes from `experimental.image_generate.model` in `opencode.jsonc` (currently `openai/gpt-image-2`); without it the tool picks automatically.
- It runs in the background and notifies the session with the saved path. Do not poll or re-request.
- The saved file takes its real format's extension (`.png`, `.jpg`, `.webp`), so use the path from the notice, not the one requested.
- An existing file at `path` is overwritten (after permission), so pick a fresh name unless the user wants a replace.
- One image per call. For N images, call N times.
- Verify: `file <path>` must say an image format. If not, report FAIL with the actual output.
- Prompt shaping and Rules below apply to this backend too.

## Codex backend

### Workflow

1. Build the prompt. Keep the user's ask, add structure if it's thin, and ALWAYS
   append this instruction verbatim:

   ```
   After the image is generated, reply with ONLY the absolute file path of the saved image, nothing else.
   ```

2. Run it non-interactively (quote the destination dir to the user's project when known):

   ```bash
   codex exec --skip-git-repo-check -s workspace-write -o /tmp/image-mill-last-msg.txt "<PROMPT>"
   ```

   - `-o` captures the final message (which should be just the image path).
   - `workspace-write` lets Codex copy the image to a destination itself.
   - Allow up to 3 minutes; image generation is slow.

3. Read the path:

   - If the user named a destination (e.g. `assets/icon.png`), include the copy
     instruction in the prompt: `Copy the generated file to <abs destination>. Reply with ONLY the absolute path of the copy.`
   - Read `/tmp/image-mill-last-msg.txt` and take the first line that ends in `.png`.
   - Fallback if the file is missing or unusable: glob the newest
     `~/.codex/generated_images/*/**.png` and use it.

4. Deliver:

   - If the image is not already at the user's destination, `cp` it there.
   - Default destination when the user didn't name one: `./generated/<descriptive-name>.png` in the project root (create the dir if needed).
   - Report the final absolute path to the user. For preview-only requests (no project attachment), reporting the Codex-generated path is enough.
   - Never leave a project-bound asset only under `~/.codex/generated_images/`.

5. Verify before reporting: `file <path>` must say PNG image data. If not, report FAIL with the actual output.

### Prompt shaping

Pass the user's intent through with light structure — do not add creative
requirements they didn't ask for. Useful lines when relevant:

```
Use case: <logo-brand | ui-mockup | illustration-story | product-mockup | photorealistic-natural | stylized-concept>
Primary request: <user's ask verbatim>
Constraints: <no text, no watermark, transparent background, etc.>
```

- Quote any exact text to appear in the image verbatim.
- For edits of an existing local image, attach it: `codex exec -i <file> ...` and
  describe the edit with invariants ("change only X; keep Y unchanged").

## Rules

- One image per `codex exec` call (or built-in tool call). For N images, run N calls (sequentially is fine).
- Never echo Codex auth/config contents; never log tokens or keys.
- Do not modify anything under `~/.codex/skills/` — Codex owns its system skills.
- Don't hijack: this skill is only for raster/bitmap generation requests. SVG,
  diagrams, and code-native graphics do NOT belong here.