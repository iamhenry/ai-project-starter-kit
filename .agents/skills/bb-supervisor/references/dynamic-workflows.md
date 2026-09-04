# Dynamic BB Workflows

Read this file only after a Mission qualifies for a dynamic BB Workflow.

## Qualification

Use a Workflow when predictable multi-stage sequencing, parallel fan-out, preview, or resumption provides concrete value. Directly invoke a canonical skill for ordinary work. Never create a one-stage Workflow.

A Workflow coordinates execution only. It never owns or mutates Task lifecycle or Mission section state.

## Run Lifecycle

Generate the smallest inline JavaScript needed for the selected deterministic stages.

```bash
bb workflows validate --script '<javascript>'
bb workflows run --script '<javascript>' --args '<json>'
bb workflows status <run-id>
bb workflows history <run-id> --cursor <call-index> --limit <1-100>
```

Capture the returned run ID and preview directive. Report after the run starts so the Supervisor can record the ID, then report the terminal result. Copy the preview directive exactly once in the Mission response.

Resume an interrupted resumable run only in the same Mission environment, using the same script and arguments plus `--resume <run-id>`. Never resume or rerun a completed run merely to recover evidence; inspect it by run ID.

Record the active or latest run ID in `WORKFLOW_RUN`; use `none` when no Workflow is warranted.

## Canonical Skill Stages

Treat an orchestration-heavy skill as one skill-owned Workflow stage. Tell that stage's Worker to load the canonical skill by name and follow it exactly; never copy, flatten, reduce, or reinterpret the skill contract in JavaScript.

The skill still owns its complete topology, Workers, artifacts, gates, retry rules, and stop conditions. For example, `gather-context` must perform its full internal fan-out and produce every required artifact.

Propagate every canonical `ASK_USER`, blocker, review failure, retry rule, and hard stop. Never choose or continue on the skill's behalf. Keep stage internals inside the Mission and report only boundary results upward.
