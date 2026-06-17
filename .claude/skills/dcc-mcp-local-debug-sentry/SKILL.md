---
name: dcc-mcp-local-debug-sentry
description: Use when a DCC MCP task needs local gateway/server debugging, Sentry-backed error capture, `vx sentry-cli` issue/event inspection, or routing a reproducible local-debug failure to the DCC MCP Backend/Core squad.
---

# DCC MCP Local Debug With Sentry

Use this skill when a Multica issue mentions DCC MCP local debug, local service startup, Sentry, `vx sentry-cli`, gateway/server diagnosis, or a hard-to-locate adapter/core failure.

## Safety Boundary

- Never paste Sentry auth tokens, DSNs, webhook URLs, local-only secrets, raw crash payloads, or full logs into Multica or GitHub.
- GitHub public text must stay English and public-safe. Keep Sentry event IDs, local paths, and internal routing inside Multica.
- Use `best-ai-dev` as the Sentry org. Prefer a DCC-specific project when available; otherwise use `dcc-mcp-core` as the fallback project until a narrower project exists.
- Project creation/key management may require account-level permissions. If `vx sentry-cli` can list but API/project-key operations return 403, create a compact Multica issue for CI/DevOps/Release or hallong rather than blocking debug work.

## Project Selection

Run:

```powershell
vx sentry-cli info
vx sentry-cli projects list --org best-ai-dev
```

Use this order:

1. `dcc-mcp-local-debug` for local gateway/server/DCC service debugging, if it exists.
2. `dcc-mcp-automation-debug` for Multica agent/runtime/autopilot harness errors, if it exists.
3. `dcc-mcp-core` as the current fallback project.

Do not assume DSN access from project visibility. If no DSN is available in the environment, ask for the DSN to be configured outside chat or route a permissions/setup issue.

## Environment Setup

Set these only in the current shell/process:

```powershell
$env:SENTRY_ORG = "best-ai-dev"
$env:SENTRY_PROJECT = "dcc-mcp-core"
$env:DCC_MCP_SENTRY_DSN = $env:DCC_MCP_SENTRY_DSN
$env:DCC_MCP_SENTRY_ENVIRONMENT = "local-debug-$env:USERNAME"
$env:DCC_MCP_SENTRY_SAMPLE_RATE = "1.0"
$env:DCC_MCP_SENTRY_RELEASE = "dcc-mcp-core@$(git -C G:\PycharmProjects\github\dcc-mcp-core rev-parse --short HEAD)"
$env:RUST_LOG = "info,dcc_mcp=debug,dcc_mcp_gateway=debug,dcc_mcp_server=debug"
```

If `DCC_MCP_SENTRY_DSN` is empty, Sentry capture is disabled by design. Continue with local logs, but record `sentry_dsn_missing=true` in the Multica issue metadata and route setup if Sentry evidence is required.

## Start Local Services

Use the repo script when working from `G:\PycharmProjects\github\dcc-mcp-core` or a clean task worktree:

```powershell
cd G:\PycharmProjects\github\dcc-mcp-core
.\scripts\cli-gateway-debug.ps1 -Mode standalone -McpPort 18765
```

For a live DCC + gateway session after relinking the adapter to the local core:

```powershell
cd G:\PycharmProjects\github\dcc-mcp-core
.\scripts\cli-gateway-debug.ps1 -Mode gateway -BaseUrl http://127.0.0.1:9765
```

The standalone mode starts `dcc-mcp-server` with example skills and runs CLI health/smoke/search checks. The gateway mode expects a live gateway and validates health/list/smoke/search.

## Sentry Probe

After setting `SENTRY_ORG` and `SENTRY_PROJECT`, send a harmless probe:

```powershell
vx sentry-cli send-event --message "dcc-mcp local debug probe" --level info --env $env:DCC_MCP_SENTRY_ENVIRONMENT --release $env:DCC_MCP_SENTRY_RELEASE --tag component:local-debug --tag source:multica
```

Then inspect recent Sentry state:

```powershell
vx sentry-cli issues list --org best-ai-dev --project $env:SENTRY_PROJECT --status unresolved
vx sentry-cli events list --org best-ai-dev --project $env:SENTRY_PROJECT
```

When the user asks for "current" Sentry errors, do not rely on unresolved issue lists alone. Verify recent events and report whether the issue has events in the requested time window.

## Debug Evidence To Capture

Keep the Multica comment compact:

- Repo/worktree and git head SHA.
- Mode: `standalone` or `gateway`.
- Sentry org/project and environment tag, but not DSN.
- Exact command category run, not raw secrets or huge logs.
- Failing check or exception summary.
- Sentry issue/event ID or URL when available.
- Next owner and acceptance criteria.

## Routing

Route to `dcc-mcp 后端/Core 小队` when:

- The failure reproduces in standalone mode.
- Sentry shows a Rust panic, gateway/server error, schema/protocol issue, or missing instrumentation in `dcc-mcp-core`.
- Adapter behavior depends on a missing or unstable core contract.

Route to `dcc-mcp CI/DevOps/Release 小队` when:

- Sentry project/key/DSN setup is missing or returns 403.
- CI Sentry E2E is failing or the GitHub secret `DCC_MCP_SENTRY_DSN` needs verification.
- The problem is workflow, release, or account configuration rather than code.

Route to `dcc-mcp Docs/Knowledge 小队` when:

- The fix is documenting local debug steps, AGENTS/llms guidance, or a runbook drift.

## Core Follow-Up Template

If a core change is required, create one compact Multica issue in project `dcc-mcp-core`:

```text
Title: Add/repair DCC MCP local debug Sentry instrumentation for <component>

Goal:
Make <component> failures visible in local-debug Sentry sessions without exposing DSNs or raw local paths.

Evidence:
- Mode:
- Repo/head:
- Sentry project/environment:
- Event/issue:
- Reproduction command:

Acceptance:
- Local standalone/gateway run captures the target failure or breadcrumb.
- Sentry disabled path remains zero-config and quiet when DSN is absent.
- Tests/docs cover the new instrumentation or runbook behavior.
- Public PR metadata is English and public-safe.
```
