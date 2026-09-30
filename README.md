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

## Council workflow

.bb/workflows/council.js is a dependency-free BB Workflow port of
RoderickOxen/opencode-council at commit
066b2add1c831d5ba1843695171c72879edb2d45. It runs Researcher, Logician,
Creative, and Critic openings, rotating proposals, parallel votes, revisions,
and a non-voting Synthesizer. The result reports consensus or dissent, the
rounds used, a final vote summary, and (only with debug: true) the complete
transcript.

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
| `ffmpeg` | Frame extraction, video verification (viral/remotion skills) | `brew install ffmpeg` |
| `yt-dlp` | Video downloads (viral-research) | `brew install yt-dlp` |

### Apps (not CLIs)
- **Xcode** — required by all iOS tooling above (simulators, signing).
- **Astro** (https://astro.app) — Mac app required by the ASO and
  keyword-research skills (local ASO database queries).
