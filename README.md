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

`.bb/workflows/council.js` is a dependency-free BB Workflow port of
[RoderickOxen/opencode-council](https://github.com/RoderickOxen/opencode-council)
at commit `066b2add1c831d5ba1843695171c72879edb2d45`. It runs Researcher,
Logician, Creative, and Critic openings, rotating proposals, parallel votes,
revisions, and a non-voting Synthesizer. The result reports `consensus` or
`dissent`, the rounds used, a final vote summary, and (only with `debug: true`)
the complete transcript.

Validate it locally from this repository:

```bash
bb workflows validate --name council
```

The question must be at least 10 characters. `maxRounds` accepts 1–5 and
defaults to 3; `consensusMode` defaults to `unanimous`. Every worker defaults to
`opencode` / `openai/gpt-5.6-luna` / `low`. BB requires provider, model, and
reasoning level to be source-level string literals. To change the model, edit
the three literals together at the shared `agent()` call site in
`.bb/workflows/council.js`, then revalidate:

```bash
bb workflows validate --name council
```

To dispatch it as a reusable global workflow, install the `global-workflows`
plugin and set its `catalogDir` to this repository's absolute `.bb/workflows`
directory. Confirm that the catalog is visible:

```bash
bb global-workflows list
```

Dispatch it with the installed plugin using the global-workflows command shape
`bb global-workflows run <name> [--thread <id>] [--args <json>]`:

```bash
bb global-workflows run council --thread <thread-id> --args '<json>'
```

`global-workflows` delegates execution, card, and history handling to BB's
builtin workflows. The worker prompt permits codebase and web research but
prohibits writes. Model changes remain source literals: edit the three literals
together at the shared `agent()` call site in `.bb/workflows/council.js`, then
revalidate.

For the dependency-free deterministic protocol check, run:

```bash
node .bb/checks/council-workflow.js
```

### Attribution and license

This port preserves the upstream MIT attribution:

```text
MIT License

Copyright (c) 2026 RoderickOxen

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

## Purpose

This starter kit is designed to:
- Accelerate project setup and planning
- Ensure consistent documentation
- Optimize interaction with AI coding assistants
- Provide structure for complex software projects
