# Project Starter Kit

A comprehensive starting point for software development projects that leverages AI-assisted code generation and structured planning.

## Overview

This starter kit provides a foundation for new software projects with a focus on organized documentation and AI-assisted development. It includes templates and documentation structures designed to streamline the development process from planning to implementation.

## Features

- **AI-Assisted Code Generation Templates**: Pre-defined templates optimized for AI code generation tools
- **Structured Documentation**: Frameworks for planning and documenting your software projects
- **Development Workflow Guides**: Best practices for organized development

## Getting Started

1. Clone this repository as a base for your new project
2. Explore the documentation in the `docs` folder for templates and guides
3. Adapt the structure to fit your specific project needs

## Documentation

The `docs` directory contains various templates that serve as:
- Project planning frameworks
- AI prompt templates for code generation
- Architecture design documents
- Development workflow guidelines

## Purpose

This starter kit is designed to:
- Accelerate project setup and planning
- Ensure consistent documentation
- Optimize interaction with AI coding assistants
- Provide structure for complex software projects

## Tooling & Dependencies

CLIs this repo's skills and workflows assume are installed on the machine.
Per-project runtime binaries (Remotion, shadcn, react-grab) are excluded —
they install with each project, not the machine.

**Base prerequisite:** Node.js + npm (most tools below install through it).

### Core agent tooling
| Tool | Purpose | Install |
| --- | --- | --- |
| `bb` | BB CLI — projects, threads, environments, skills | ships with BB |
| `opencode` | OpenCode — agents, subagents, second opinions | `npm i -g opencode-ai@latest` |
| `codex` | Codex CLI — image generation (image-mill), coding agent | OpenAI install |
| `gh` | GitHub CLI — issues, PRs, external repo access | `brew install gh` |
| `agent-browser` | Browser automation for web testing and QA | `npm i -g agent-browser && agent-browser install` |
| `cua-driver` | Drive native macOS/Windows/Linux GUI apps | install per cua-driver docs |

### iOS / App Store tooling
| Tool | Purpose | Install |
| --- | --- | --- |
| `xcodebuildmcp` | XcodeBuildMCP CLI — iOS/macOS build, test, log | `brew install xcodebuildmcp` (or `npm i -g xcodebuildmcp@latest`) |
| `asc` | App Store Connect CLI — builds, uploads, TestFlight | `brew install asc` |
| `argent` | Drive simulators/devices, QA flows, profiling | `npm i -g @swmansion/argent` |
| `agent-device` | Declarative UI automation for iOS/Android devices | [callstack/agent-device](https://github.com/callstack/agent-device) |
| `expo` | Expo CLI — dev server, localization QA, verification | `npm i -g expo` |

### Utility CLIs
| Tool | Purpose | Install |
| --- | --- | --- |
| `tmux` | Background processes, dev servers | `brew install tmux` |
| `jq` | JSON processing in skill pipelines | ships with macOS (`/usr/bin/jq`) |
| `ffmpeg` | Frame extraction, video verification (viral/remotion/watch-video skills) | `brew install ffmpeg` |
| `yt-dlp` | Video downloads (viral-research) | `brew install yt-dlp` |
| `whisper-cli` | Speech transcript for watch-video | `brew install whisper-cpp` (may upgrade `sdl3`/`sdl2-compat`) |

**watch-video** ([SKILL.md](.agents/skills/watch-video/SKILL.md)): local transcript + frame sheets from a screen recording with spoken commentary. Needs Python Pillow (`python3 -m pip install --user pillow`, about 15 MB) and Whisper models (~143 MB, cached in `~/.cache/whisper`), which are not auto-downloaded; run the one-time setup in SKILL.md, which lists the SHA-256 checks. Linux: same code, setup untested (see SKILL.md).

### Apps (not CLIs)
- **Xcode** — required by all iOS tooling above (simulators, signing).
- **Astro** (https://astro.app) — Mac app required by the ASO and
  keyword-research skills (local ASO database queries).

## BB Plugins

Enabled plugins beyond what ships with BB (built-ins are omitted; 30 total). Install with
`bb plugin install <source>`; catalog entries install by name.

| Plugin | What it does | Source |
| --- | --- | --- |
| Agent Calendar | Calendar / time sheet of what agents worked on | catalog: `agent-calendar` |
| Lanes | Live timeline with a lane per agent thread | catalog: `agent-lanes` |
| Agentic Mermaid | Better Mermaid rendering in chat | catalog: `agentic-mermaid` |
| Beautiful Chat | Restyles chat in BeautifulUI design | catalog: `beautiful-chat` |
| Chat Timestamps | Message times in chat action strip | `github.com/pixexid/bb-plugin-chat-timestamps` |
| Cursor Sidebar | Cursor-style sidebar: trees, pins, folders | local: `~/src/bb-plugin-cursor-sidebar` |
| Dashboard Sidebar | Project-grouped threads with status, git context, snooze | local: `bb-plugin-dashboard-sidebar` |
| Diff Editor | Edit diffs in place and save to disk | `github.com/CostaFot/bb-plugin-diff-editor` |
| Diff Viewed | "Viewed" checkbox per changed file | catalog: `diff-viewed` |
| Doc Review | Comment on MD/PDF/Office/HTML files, hand to an agent | catalog: `doc-review` |
| Fast Split | One-click neighbouring new-thread pane | catalog: `fast-split` |
| File Manager | Browse/upload/download/move files under home | catalog: `file-manager` |
| File Links | Clickable file names, copy/reveal menu, image thumbnails in timeline | `github.com/adam-tracht/bb-plugin-file-links` |
| Files | VS Code-style file explorer and editor | catalog: `files-editor` |
| Finder | File tree, editor, and markdown preview for a workspace | catalog: `finder` |
| Fluid Thinking | Thinking indicator for timeline turns | `github.com/fahmiirsyadk/bb-plugins` |
| Generative UI | Agents answer with inline interactive UI | `github.com/ComicBit/bb-plugin-genui` |
| Git History | Full Git history in a right panel | catalog: `git-history` |
| Git worktree | Stage, AI-commit, branch, sync in BB | catalog: `git-panel` |
| Gitx | VS Code-style source control sidebar | local: `bb-plugin-gitx` |
| Host Monitor | Resource health across enrolled machines | catalog: `host-monitor` |
| Image Preview | Click-to-expand chat image previews | catalog: `image-preview` |
| Inline Comments | Quote reply text as comments in next message | catalog: `inline-comments` |
| Missing keyboard shortcuts | Shortcuts for threads, history, composer | `github.com/ariofrio/ribbon` |
| OpenCode | Run BB threads on a detached OpenCode server | `github.com/iamhenry/bb-opencode` |
| Pins | Pinned threads in a live-chat strip | local: `bb-plugin-pins` |
| Preset Buttons | One-click provider/model presets in New thread | catalog: `preset-buttons` |
| Session Brief | Floating snapshot: context, usage, subthreads, todos | local: `bb-plugin-session-brief` |
| Usage | Token usage and estimated cost per machine | catalog: `usage` |
| Vercel Theme | Vercel-style palette and Geist type | catalog: `vercel-theme` |
| Workbench Explorer | File explorer beside every thread | catalog: `workbench-explorer` |

Local plugins live under `~/Desktop/Projects/other/` (Cursor Sidebar: `~/src/`);
install with `bb plugin install <path>`.
