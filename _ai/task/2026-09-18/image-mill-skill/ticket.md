# image-mill skill

**Date:** 2026-09-18
**Status:** done

## Problem

OpenCode has no image generation capability. Codex CLI (installed, v0.154.0) has a
built-in `image_gen` tool that saves PNGs under `~/.codex/generated_images/<session>/`.
A verified non-interactive path exists:

```
codex exec --skip-git-repo-check -s workspace-write -o <msg-file> "<prompt asking for image + path reply>"
```

Final message can be made to contain only the absolute PNG path; with
`workspace-write`, Codex can also copy the file to a destination directly
(verified: `/tmp/codex-img-test/star.png`).

## Goal

Create a simple OpenCode skill named `image-mill` at
`/Users/macvm/.config/opencode/skills/image-mill/SKILL.md` that:

1. Checks `codex` is installed (report BLOCKED with install hint if not)
2. Runs `codex exec` non-interactively with a structured image prompt
3. Retrieves the generated PNG (from Codex's final message, or newest file in
   `~/.codex/generated_images/` as fallback)
4. Copies it to the requested destination (or a sensible default in cwd)
5. Reports the final path

Tool-agnostic name on purpose: more CLI backends may be added later.

## Constraints

- Keep the skill super simple (single SKILL.md, no scripts)
- Never log or echo secrets
- Don't modify Codex's own system skills
- Skill must state its trigger conditions so it doesn't hijack non-image prompts

## Verification contract

- Observable: user asks OpenCode to "generate an image of X", skill fires,
  codex generates, and the image file exists at a user-visible path in the project
- Receipt: generated PNG path + `file` output proving it's a valid PNG
- Probe: run the skill's documented flow once on a real prompt; verify PNG exists

## Reference

- Source thread: thr_5rs82fp5b3 (test image generation with Codex)
- Codex system skill for reference shape: `~/.codex/skills/.system/imagegen/SKILL.md`
- Prior live smokes: apple PNG (1254×1254) at
  `~/.codex/generated_images/01a0b5b6-.../exec-15cc4f7b-....png`;
  star copied to `/tmp/codex-img-test/star.png`