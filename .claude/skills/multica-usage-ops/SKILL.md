---
name: multica-usage-ops
description: Operate Multica efficiently across agents, squads, issues, projects, autopilots, skills, imports, prompt optimization, harness-engineering operating model, specialized dcc-mcp squad routing, dynamic assignee/status flow control, Headroom context compression, CodeGraph indexed search, timer governor design, daily PM research/RFC proposal gates, human decision escalation to hallong, DCC MCP squad self-loop workflows, GitHub issue/PR association routing, dcc-mcp-core release downstream loops, agent-first cleanup/docs automation, PR CI handoff gates, single-hop mention safety, and public-safe GitHub boundaries.
---

# Multica Usage Ops

Use this skill when the user asks to operate Multica efficiently, manage Multica agents, squads, issues, projects, autopilots, skills, imported skills, agent prompts/instructions, runtime/daemon state, or dcc-mcp team self-loop workflows. Use especially when the user says things like "帮我优化 DCC MCP 开发小队的 agent 提示词", "让小队完整自循环", "导入/挂载/更新 skill", "用 multica 创建/分配/推进 issue", or "清理/忽略 multica 临时文件".

## Source Of Truth

- Inspect live state first with `multica` and, for GitHub-related work, `gh`.
- Prefer official Multica docs when CLI behavior is unclear:
  - CLI reference: https://multica.ai/docs/zh/cli
  - Agents: https://multica.ai/docs/zh/agents
  - Agent configuration: https://multica.ai/docs/zh/agents-create
  - Skills: https://multica.ai/docs/zh/skills
  - Autopilots: https://multica.ai/docs/zh/autopilots
  - Architecture: https://multica.ai/docs/zh/how-multica-works
- Treat IDs, runtime status, hooks, skills, and agent instructions as drift-prone. Re-read before editing.

## Core Principles

- Multica server stores workspace data and task queues; agent execution happens through local daemon/runtime and local AI coding tools.
- Assigning an issue, mentioning an agent, direct chat, and autopilots are different trigger paths. Choose the smallest path that fits the work.
- `run_only` autopilot mode is not read-only. It only prevents Multica from creating a wrapper issue for the autopilot run; the agent must still create/update durable Multica issues, Multica comments, assignees, statuses, metadata, and public-safe GitHub labels when the patrol finds actionable work. GitHub comments are exceptional and allowed only for external/public communication in concise English.
- Workspace skills are the team-sharing default. Local skills are for experiments or sensitive local-only content.
- A skill must be attached to an agent to take effect, and only new tasks pick up edited skill content.
- Agent `instructions` are prepended to every task. Keep them role-specific, operational, and safe.
- Do not store high-value secrets in agent custom env. Use limited-scope credentials and avoid exposing env, webhook URLs, PATs, or local paths in comments.
- Use `create_issue` autopilot mode for durable work unless the user explicitly wants fire-and-forget `run_only`.

## Harness Engineering Operating Model

Use a harness-first design for the DCC MCP automation system: prompts are not enough. The durable harness is the combination of repo docs, skills, autopilot triggers, compact state, issue metadata, CI/review feedback, and cleanup loops.

Principles:

- Keep the system of record small and navigable. `AGENTS.md`, skills, runbooks, ADRs, and issue metadata should point agents to authoritative code/docs instead of duplicating whole payloads.
- Make the harness agent-legible. Every durable issue should expose repo, owner, current phase, acceptance criteria, gate checklist, next check time, and exact wake-up mechanism.
- Prefer event hooks for fast paths and scheduled heartbeats for missed-event recovery. Timers should recover state, not create duplicate work.
- Use feedback loops as first-class inputs: CI result, review decision, merge state, release notes, codegraph impact, and docs drift all update status/metadata before routing.
- Build cleanup into the harness. Temporary files, stale generated docs, obsolete branches/issues, duplicate wrapper issues, long raw payloads, and invalid public references are entropy and should be collected.
- Agent-first by default: agents execute routine code cleanup, docs updates, CI repair, PR handoff, and release-train work. Humans decide product direction, credentials, paid/risky changes, sensitive disclosure, and ambiguous release policy.
- Public systems get public-safe summaries only. Multica carries internal reasoning, routing, issue IDs, and sensitive discussion.

## Timer Governor

Use three timer classes instead of one broad cron:

- `event_handler`: webhook-triggered fast path. It must classify the event, create/update one compact canonical issue, and no-op on mismatched conclusions/actions.
- `heartbeat`: scheduled recovery. It scans bounded active state and repairs missed assignments, stale statuses, missed releases, or missed PR transitions.
- `gardener`: scheduled maintenance. It performs cleanup, docs drift checks, automation health checks, and context-index hygiene.

Required governor rules for scheduled autopilots:

- Stagger schedules so major automations do not all start on minute `0`. Current default layout: release fallback `0,30`, PR/self-loop heartbeat `5,35`, status recovery `10,40`, automation health `20 */4`, docs gardener `15 4`, code cleanup `30 3`.
- At run start, check recent runs for the same autopilot. If another run is active or newer than the safe overlap window, exit with `no_action_timer_overlap`.
- Bound work per run: default maximum 10 issues, 20 PRs, 5 repos, and 3 child issues unless the user explicitly names a target.
- Always prioritize active `in_progress` projects, urgent/high priority issues, stale PR gates, and human-decision blockers before broad scans.
- Use `next_check_at`, `pipeline_phase`, `review_status`, `blocked_reason`, and association metadata so the next heartbeat knows why work was skipped.
- Do not write raw event payloads, complete CLI JSON, or full logs into Multica issues. Link to source and store a compact association block.
- A scheduled autopilot must not finish with report-only output when it found actionable work. It must mutate state through create/update/assign/comment/rerun/status/metadata or explicitly record `no_action_*`.

## Provider Balance And Model Retry Policy

Treat provider quota/billing failures as recoverable runtime blockers first, not as task completion or product blockers.

- If a run reports `API Error: 402 Insufficient Balance`, `insufficient balance`, `quota exceeded`, or equivalent provider-billing text, record `metadata.provider_error=402_insufficient_balance` and the model/provider if visible.
- Retry once when the underlying work is still actionable: rerun the same issue/assignee after a short wait, or route to an equivalent cheaper/available model/runtime when the agent has a known role-compatible fallback.
- Preferred low-risk free fallback: `opencode/deepseek-v4-flash-free` via `小白` for patrol triage, issue compaction, docs/skills cleanup, metadata repair, and non-destructive audit work.
- Do not use the free fallback as the sole authority for high-risk code review, security decisions, release policy, or final merge approval. It may prepare evidence, but loonghao/hallong or the configured lead gate remains authoritative.
- If the second attempt fails with the same balance/quota error, stop automatic retries. Set `metadata.human_decision_required=true`, `metadata.waiting_on=hallong`, and mention hallong once with exact provider/model/task evidence plus suggested fallback options.
- Do not post GitHub public comments for provider-billing failures. Keep the discussion inside Multica.
- Do not reassign to unrelated agents just to bypass cost. Use a role-compatible fallback, otherwise escalate.
- Do not mark implementation done/cancelled only because provider balance failed; keep the original work recoverable.

## Agent-First Cleanup And Docs

Cleanup is normal engineering work, not an afterthought.

- Branch discipline: before starting new repo work, refresh `remote main` and base the worktree/branch on it unless the issue explicitly targets an existing PR branch. If reusing an existing branch, rebase it onto current remote main before editing when safe.
- Merge discipline: DCC MCP PRs should use rebase merge or the repo's rebase/merge-queue equivalent. If the PR is behind or conflicts, resolve conflicts first, push the updated head, wait for CI, and then re-run exact-head review/merge gates.
- Code cleanup should be small, source-backed, and PR-based: remove dead code, stale generated files, duplicate helpers, obsolete docs, broken examples, abandoned branch metadata, and invalid public references only when evidence is clear.
- Do not perform destructive repository or branch deletion from automation unless a human explicitly approved the exact target. Prefer cleanup PRs, labels, or Multica issues.
- Completed tasks must clean their temporary worktrees and checkout artifacts when safe. Only remove worktrees that were created by the agent, `vx wt`, Codex, Cursor, or Multica for that task and are not the primary user repository.
- Before deleting any worktree, verify it has no uncommitted/unpushed task changes, no active process using it, and no active Multica issue/task still referencing it. Prefer `git worktree list --porcelain`, `vx wt list`, and explicit path checks.
- If a worktree contains unresolved or valuable changes, keep it, record the path in Multica, and mark cleanup blocked or requiring human decision instead of deleting.
- Documentation automation should keep docs close to changed behavior: README, AGENTS, llms files, skills, runbooks, ADRs, release notes, and public/private boundary notes.
- Docs gardener work must update the authoritative source first, then generated/readme surfaces. Do not paste implementation history or Multica routing into public docs.
- Every automation or agent-prompt change should leave a durable note in the relevant skill/reference or runbook so future agents inherit the rule.

## ClawSweeper-Inspired Issue And PR Maintenance

For DCC MCP automation, copy ClawSweeper's boundary rather than its public-comment behavior:

- Review/classification is proposal-only.
- Apply/mutation rechecks live state and owns closes, cancels, labels, pushes, and merges.
- Repair/edit work is agent-owned, but merge and close gates require exact live evidence.
- A PR can auto-merge only when current head SHA equals the loonghao-reviewed head SHA, required checks are green, metadata is public-safe, no security/human gate is open, and live mergeability is clean.
- Final merge should be rebase merge or the repository's configured rebase/merge-queue equivalent. Do not merge a dirty/behind/conflicting head; route conflict/base-sync repair first.
- Pending checks keep the current owner waiting; completed failing checks route repair.
- Issue cleanup is conservative: cancel duplicate Multica wrappers freely after canonical compaction, but public GitHub closes need high-confidence duplicate/superseded/implemented/fixed evidence and a public-safe reopen path.

## Discovery Checklist

Run these before making changes:

```powershell
multica auth status
multica config show
multica daemon status
multica workspace member list --output json
multica agent list --output json
multica squad list --output json
multica skill list --output json
multica autopilot list --output json --full-id
```

For a target squad:

```powershell
multica squad get <squad-id> --output json
multica squad member list <squad-id> --output json
```

For a target agent:

```powershell
multica agent get <agent-id-or-name> --output json
multica agent skills list <agent-id> --output json
multica agent tasks <agent-id> --output json
```

## Temporary File Hygiene

Never leave Multica working artifacts inside target code repositories unless they are intentional deliverables.

Use this layout for temporary material:

- Draft prompts: `work/multica-prompts/`
- Skill drafts: `work/multica-skills/`
- API/CLI response snapshots: `work/multica-snapshots/`
- Redacted verification notes: `work/multica-verification/`

Before touching a git repo, ensure these patterns are ignored or kept outside the repo:

```gitignore
# Multica/Codex temporary files
work/
*.multica.tmp
*.multica.json
*.multica.log
multica-*.tmp
multica-*.draft.*
.multica-cache/
.multica-temp/
```

Never commit webhook URLs, trigger tokens, PATs, daemon logs with secrets, or raw payloads containing private data.

## Output Hygiene

Avoid large persisted tool outputs. Many Multica issues created from webhooks can contain long descriptions unless explicitly compacted.

- Do not paste raw webhook payloads, full autopilot prompts, or full `multica issue get` JSON into Multica comments or new issue descriptions.
- Chinese GitHub comments, PR reviews, and inline review comments from `loonghao`, or on PRs submitted/authored by `loonghao`, are internal review/coordination signals. Do not reply to them publicly on GitHub; reply or route in the associated Multica issue instead.
- If the PR/issue submitter is not `loonghao`, or the commenter is an external/non-loonghao contributor who needs a public answer, a public GitHub reply is allowed only when it is public-safe and contains no Multica IDs, internal routing, private context, local paths, or raw payloads.
- Default to no GitHub public comments or reviews for Multica workflow, review handoff, CI waiting, implementation status, or internal/loonghao-owned PR coordination. Keep those updates in Multica.
- Any allowed GitHub public reply must be concise English and public-safe. Never use Chinese for GitHub public workflow/review/status comments.
- If a Chinese/internal GitHub comment was posted by mistake, delete or edit it away when permitted, record the correction inside Multica, and do not post a public replacement unless explicitly asked.
- Before routing PR review/fix work, always refresh live PR state. If `gh pr view ... --json state,mergedAt,headRefOid` says the PR is `MERGED` or `CLOSED`, stop the loop internally: mark review handoff issues done, cancel obsolete fix issues, add a compact Multica note, and do not mention another reviewer.
- If an issue contains generated webhook boilerplate beginning with `Autopilot run triggered`, `Webhook event:`, or `Webhook payload:`, ignore that whole block as transport metadata. Do not read, summarize, quote, copy, or route that raw block to another agent.
- Prefer an existing canonical compact issue for the same GitHub PR/run. If only a wrapper issue exists and the event is actionable, create/update one compact issue and cancel or compact the wrapper duplicate.
- When reading an issue, project the fields you need instead of dumping the whole object:

```powershell
multica issue get <id> --output json |
  ConvertFrom-Json |
  Select-Object id,number,title,status,assignee_id,assignee_type,metadata
```

- When webhook context is needed, keep only a compact association block: `GitHub PR/Issue`, `Repo`, `Number`, `Workflow run`, `Conclusion`, `Head branch/SHA`, `Current owner`, `Status`, `Routing signal`, and a short gate checklist.
- Prefer live GitHub URLs and `gh pr view` / `gh run view` for details instead of storing the whole payload in Multica.
- If an existing issue description is huge, compact it before handing off so downstream agents do not trigger `persisted-output` files.
- Mark cleaned issues with `metadata.payload_storage=compacted` and `metadata.ignore_raw_webhook_block=true`.

## Skill Operations

Create or update workspace skills:

```powershell
multica skill create --name <name> --description "<triggering description>" --content-file <SKILL.md> --output json
multica skill update <skill-id> --description "<description>" --content-file <SKILL.md> --output json
multica skill files upsert <skill-id> --path references/<file>.md --content-file <file> --output json
```

Import skills:

```powershell
multica skill search <query> --output json
multica skill import <url-or-source> --output json
```

Always review third-party `SKILL.md` and bundled files before import. Imported skills may contain executable scripts, and Multica hands those files to the AI coding tool as-is.

Attach skills without replacing existing assignments:

```powershell
multica agent skills add <agent-id> --skill-ids <skill-id-1>,<skill-id-2> --output json
```

Use `agent skills set` only when the user explicitly wants to replace the full skill list.

## Agent Instruction Optimization

When the user says "帮我给我们 DCC MCP 开发小队的 agent 提示词指令进行优化，确保他们能够完整的形成自循环", do this:

1. Read the squad, members, current agent instructions, assigned skills, runtimes, and recent tasks.
2. Build a role matrix: PM, tech lead/reviewer, backend, frontend, full-stack, tester, docs/ops, project manager.
3. Preserve each agent's specialty and existing useful constraints.
4. Do not paste the full shared self-loop contract into every agent. Keep agent instructions as a thin role card: identity, ownership, concrete outputs, and 5-8 hard local gates.
5. Put shared rules in workspace skills and references instead: `multica-usage-ops`, `multica-github-autopilot-ops`, and `references/dcc-mcp-self-loop-instructions.md`.
6. Attach or verify required skills:
   - `multica-usage-ops`
   - `multica-github-autopilot-ops`
   - dcc-mcp domain skills
   - language/runtime skills relevant to that agent
   - review/testing/docs skills for lead/test/docs agents
7. Update instructions with `multica agent update <id> --instructions "<text>"`. Target 500-1500 characters per agent unless a role genuinely needs more. For long drafts, store them in an ignored workspace file, read into a PowerShell variable, then pass that variable to `--instructions`.
8. Verify by re-reading each agent and checking skill assignment.

Shared self-loop contract for skills/references, not for copy-pasting into every agent:

- Intake: restate the issue goal, repo/project, acceptance criteria, and constraints.
- Context: inspect live repo/PR/issue/CI state before deciding.
- Plan: produce a small plan or split into Multica issues when the work is too large.
- Execute: work in a clean branch/worktree, keep scope narrow, and avoid unrelated changes.
- Verify: run relevant tests/checks; when external systems are involved, verify live status.
- Report: comment progress, blockers, commands run, and next action in the Multica issue.
- Handoff: if another role should continue, assign or mention the right agent/squad with concise context.
- Flow control: use assignee changes only for exclusive ownership transfer; use single-mention comments for lightweight consultation or parallel input.
- Status hygiene: keep issue status aligned with phase (`todo`, `in_progress`, `in_review`, `blocked`, `done`, `cancelled`) so patrols can recover stalled work.
- PR handoff: after pushing or force-pushing a PR branch, keep ownership until public metadata is clean and GitHub required CI/checks are green. Do not live-mention `loonghao` while checks are pending.
- Review: route code review through the technical lead and respond to feedback. The technical lead must either merge/enable auto-merge after an approving review and green gates, or route blocking feedback back to exactly one implementer with a live mention/reassignment and `todo`/`in_progress` status.
- Internal Multica review comments are not magic triggers. If loonghao writes blocking feedback in a Multica issue without a live mention/reassignment/rerun, no implementer will start. The reviewer must route in the same turn; patrol must recover by extracting the checklist, adding one live implementer mention or rerunning the assignee, and setting `review_status=changes_requested`.
- Publish: push/PR/merge only when requested and after checks/review pass.
- Close: update issue status and leave a short final comment with evidence.
- Learn: if the task reveals reusable process, update or propose a skill/reference.

Use the detailed template in `references/dcc-mcp-self-loop-instructions.md`.

For status/activity driven flow control, use `references/status-flow-policy.md`. It defines how to interpret UI statuses 审核中/进行中/阻塞中, squad activity records, review feedback recovery, and blocked issue recovery.

## DCC MCP Specialized Squads

The dcc-mcp team now uses a top-level intake squad plus four specialized execution squads:

- Top-level intake/orchestration: `dcc-mcp 开发小组` / `82e19e3b-cacb-47c8-bafa-2c17ecbf8b82`, leader `倩倩`.
- Backend/Core: `dcc-mcp 后端/Core 小队` / `78fca066-86f2-4023-83a7-885766d2afbd`, leader `爱写代码的小龙`.
- Frontend/UI: `dcc-mcp 前端/UI 小队` / `d8176812-2221-43ab-819c-492d9ef3f3dc`, leader `传林`.
- CI/DevOps/Release: `dcc-mcp CI/DevOps/Release 小队` / `92fb3bf6-f48c-4cca-bfa8-2d7bcd19a76a`, leader `代码测试`.
- Docs/Knowledge: `dcc-mcp Docs/Knowledge 小队` / `38f1c230-bb7c-4d19-a3a0-97b9e8f59b33`, leader `小白`.

Routing model:

- New GitHub issues go to the top-level intake squad first unless the first owner is already obvious.
- Backend/core/Rust/Python/Go/protocol/API/schema/adapter integration goes to Backend/Core.
- Frontend/UI/web/docs-site/dashboard/UX goes to Frontend/UI.
- CI failures, GitHub Actions, release-please, tags/releases, branch protection, PR readiness, and downstream release validation go to CI/DevOps/Release.
- Docs, README, AGENTS, llms, skills, release notes, public boundary, and knowledge maintenance go to Docs/Knowledge.
- PR CI green handoff still goes directly to `loonghao` for code-review and merge decision.
- Core release published goes to the top-level squad for release-train intake, then gets split into child work for the specialized squads.

Specialized squads do not remove the single-hop rule. A leader should choose one current owner; future owners are written as plain text or split into child issues.

## Squad Operations

For squad-level work:

```powershell
multica squad get <squad-id> --output json
multica squad member list <squad-id> --output json
multica squad update <squad-id> --instructions "<instructions>" --output json
multica squad member set-role <squad-id> <member-id> --role "<role>" --output json
```

Do not flatten all role guidance into squad instructions. Put shared operating principles in squad instructions and role-specific behavior in each agent's instructions.

After a squad task, the leader should record evaluation when appropriate:

```powershell
multica squad activity <issue-id> <action|no_action|failed> --reason "<short reason>"
```

## Issue And Project Operations

Create durable work:

```powershell
multica issue create --title "<title>" --description-file <description.md> --assignee-id <agent-or-squad-id> --priority <priority> --output json
```

Assign or reassign:

```powershell
multica issue assign <issue-id> --to-id <agent-or-squad-id> --output json
multica issue status <issue-id> <status> --output json
```

Use comments for traceable progress and handoff:

```powershell
multica issue comment add <issue-id> --content-file <comment.md> --output json
```

## Dynamic Assignment And Status Flow

Use assignee as the single durable owner for the current phase, not as a generic notification tool.

Official behavior to design around:

- Assigning a non-`backlog` issue to an agent/squad enqueues a task for that assignee.
- Assigning a `backlog` issue does not start the agent until the issue moves to `todo` or `in_progress`.
- Reassigning cancels all active `queued` / `dispatched` / `running` tasks on that issue and enqueues the new assignee if eligible.
- A comment mention triggers the mentioned agent without changing assignee or status.
- `multica issue rerun <issue-id>` starts a fresh task for the current assignee and is for recovery, not for handoff.

Recommended ownership model:

- Exclusive phase owner: change assignee and set status.
- Lightweight advice/review without ownership transfer: add one single-mention comment and keep assignee unchanged.
- Parallel work: split into child issues instead of reassigning one issue back and forth.
- Recovery of a stuck current owner: inspect `multica issue runs`, use `multica issue rerun <issue-id>` when the current assignee should try again, or `multica issue cancel-task <task-id> --issue <issue-id>` for a specific bad run.

Recommended status meanings for dcc-mcp:

- `backlog`: parked; do not expect an agent to start.
- `todo`: ready for the assigned owner to start or restart.
- `in_progress`: current assignee owns execution or is waiting for CI it started.
- `in_review`: waiting for a review gate. The gate may be `code_review`, `qa_review`, `product_acceptance`, or `intake_review`; distinguish it with metadata.
- `blocked`: needs external input, missing access, upstream release, or human decision.
- `done`: acceptance criteria met, CI/review gates satisfied, and final evidence posted.
- `cancelled`: duplicate, no_action, obsolete, or intentionally stopped.

UI status mapping:

- 审核中 = `in_review`
- 进行中 = `in_progress`
- 阻塞中 = `blocked`

Dedicated status recovery autopilot:

- Title: `Multica 状态机回收：审核中/进行中/阻塞中`
- ID: `c402be53-ab90-4bd9-bc82-bf633b1c6f8b`
- Assignee: `倩倩`
- Mode: `run_only`
- Schedule: every 15 minutes from 09:00 to 23:59 Asia/Shanghai

Status recovery rules:

- `in_review` is not a passive parking lot. It must name the current review gate with metadata such as `pipeline_phase=intake_review`, `review_status=awaiting_loonghao`, `review_status=changes_requested`, `review_status=approved`, `qa_review`, or `product_acceptance`.
- If `in_review` has a PR and the head is ready for code review, trigger `loonghao` exactly once for the current head SHA.
- If `in_review` contains blocking loonghao/QA/product feedback, move it back to `todo` or `in_progress`, set `review_status=changes_requested`, and rerun/reassign the implementer. A plain comment without `mention://agent`, reassignment, or rerun does not start work.
- If `in_review` is intake review and all intake fields are complete, promote it to `todo` and assign the first implementation owner. If not complete, keep `in_review` and ask exactly one owner for the missing decision.
- `in_progress` with an active run should not be disturbed. `in_progress` without an active run and without a valid wait reason should be rerun or re-routed.
- `blocked` must be classified. Agent-actionable blockers move back to `todo`/`in_progress` with a concrete owner. Human-decision blockers stay `blocked`, mention `hallong` once, and store `human_decision_required=true`, `waiting_on=hallong`, and `pipeline_phase=human_decision`. External wait blockers stay `blocked` with `blocked_reason`, `waiting_on`, and `next_check_at`.

Safe handoff order for agents:

1. Add a concise handoff comment with evidence and exactly one next owner in plain text or one live mention, depending on whether ownership changes.
2. Set the status for the next phase, for example `multica issue status <issue-id> in_review --output json`.
3. If the next phase should be exclusively owned by another agent/squad, run `multica issue assign <issue-id> --to-id <agent-or-squad-id> --output json` as the final mutation, then stop. Reassignment can cancel the currently running task, so do not expect to perform more work afterward.

Do not use assignee changes to wake an agent that should merely inspect a comment. Use a single live mention for that path.

## Intake Review Gate

Use this when a request is not ready for implementation yet.

Meaning:

- `status = in_review` + `metadata.pipeline_phase = intake_review` means the issue is waiting for PM/intake to collect enough information before implementation.
- "intake 回收" means converting a vague/linked/request issue into implementation-ready work: repo/project, problem statement, acceptance criteria, priority, first owner, dependencies/blockers, GitHub association, and public/private boundary are clear.
- Do not assign directly to developers while the issue is in intake review unless the implementation owner and acceptance criteria are already clear.

Intake-ready checklist:

- `Repo` or project is known.
- Work type is clear: bug, feature, docs, tests, release, CI, or triage/no_action.
- Acceptance criteria are concrete enough for an agent to verify.
- Priority is set.
- First implementation owner can be chosen from role routing.
- No unresolved product/technical question blocks starting.
- For GitHub-linked work, the GitHub issue/PR URL and labels/assignees are recorded.

Automation rule:

- If `pipeline_phase=intake_review` and the checklist is incomplete, keep `in_review`; single-mention `晓黎` for product/acceptance gaps, `倩倩` for scheduling/splitting gaps, or `loonghao` for technical ownership gaps.
- If the checklist is complete, comment the intake summary, set `metadata.pipeline_phase=implementation_ready`, set status `todo`, then assign to the concrete first owner as the final mutation.
- If intake decides no implementation is needed, comment the reason, set `metadata.pipeline_phase=no_action`, then set status `cancelled` or `done` depending on whether there is a durable outcome.
- If the work is too large for one owner, keep the parent in `in_review`, create or identify child issues for implementation, and mark the parent metadata with `pipeline_phase=split_to_children`.

## Human Decision Escalation

Use this when automation cannot safely choose for the human owner.

Escalate to `hallong` for credentials, paid/budget choices, external account settings, release policy, sensitive/private information boundaries, local-only DCC/UI access, cross-repo high-risk merge or rollback decisions, and ambiguous product/business tradeoffs.

Do not only write "blocked". Add one Multica comment with exactly one live human mention:

```markdown
[@hallong](mention://member/c73ed444-85e7-407f-ac76-cc71fd7c2648)
```

The escalation comment must include:

- The exact decision needed.
- The current context and evidence.
- Options A/B/C when there is more than one viable path.
- The recommended option.
- Risk, cost, or deadline tradeoff.
- What the team will do immediately after the answer.

Set metadata so patrols can recover the issue:

- `metadata.human_decision_required = true`
- `metadata.waiting_on = hallong`
- `metadata.decision_owner_member_id = c73ed444-85e7-407f-ac76-cc71fd7c2648`
- `metadata.pipeline_phase = human_decision` when the issue is in decision review.

Use status `blocked` when the decision prevents execution. Use `in_review` plus `pipeline_phase=human_decision` when the decision is a review gate but the issue is otherwise understood.

Avoid duplicate pings. If there is already an unresolved human-decision comment for the same question, keep metadata/status current and add no-mention progress only when new evidence changes the decision.

Public boundary: keep Multica issue IDs, internal comments, private reasoning, and sensitive payloads inside Multica. If the same blocker must be reflected on GitHub, write only a public-safe statement such as "waiting for maintainer decision on release policy" without Multica IDs or internal detail.

## Product Research And RFC Gate

Use the daily PM research/RFC workflow for product discovery, not implementation.

- Assignee: product owner `晓黎` (`d142f29c-305c-4313-98f2-963621347478`).
- Schedule: daily 09:00 Asia/Shanghai via the autopilot `每日 DCC MCP 产品调研/RFC 提案`.
- Research scope: recent competitor movement, MCP skills, DCC/AI/DCC automation news, GitHub releases/issues/PRs, and official release notes or docs relevant to the DCC MCP org.
- Output must be RFC candidates tied to current DCC MCP projects, not a generic news digest.
- Each RFC candidate must include evidence links/dates, target user, affected repo/module, expected benefit, effort/risk, suggested owner/squad, acceptance criteria, blockers, and recommended priority.
- Classify candidates as `recommend_for_decision`, `watch_only`, or `no_action`.
- If a real decision is needed, set `metadata.pipeline_phase=product_rfc_review`, `metadata.human_decision_required=true`, `metadata.waiting_on=hallong`, and `metadata.decision_owner_member_id=c73ed444-85e7-407f-ac76-cc71fd7c2648`, then mention hallong exactly once.
- Do not create implementation child issues, assign development agents, or create public GitHub issues/PRs until hallong explicitly approves the RFC.
- After approval, split implementation into child issues and route by specialized squad. Keep GitHub public content English and public-safe.

## Context Optimization With Headroom And CodeGraph

Use this for dcc-mcp repos and other large codebases so agents do not waste context on broad file dumps, raw CI logs, or repeated grep loops.

Installed local MCP servers for the dcc-mcp agents:

- `headroom`: `headroom mcp serve`
- `codegraph`: `codegraph serve --mcp`

Operating rules:

- Before broad exploration in a repo, check CodeGraph state with `vx codegraph status <repo>`. If missing, run `vx codegraph init -i <repo>`. If stale after edits or branch changes, run `vx codegraph sync <repo>`.
- Prefer CodeGraph for architecture, symbol, callers/callees, impact, affected tests, and "where is this implemented" questions. Use `vx codegraph query`, `callers`, `callees`, `impact`, `affected`, or the codegraph MCP tools before falling back to raw `rg`.
- Prefer semantic reduction before output compression: `vx gh --json --jq`, `vx rg -n -m <N>`, `vx git diff --stat`, `vx git diff --name-only`, and `vx codegraph` queries.
- Use `vx --compact ...` for broad logs or subprocess output when JSON/filtered queries are not enough.
- Use Headroom MCP tools (`headroom_compress`, `headroom_retrieve`, `headroom_stats`) for large tool outputs, CI logs, search results, generated files, API payloads, and long Markdown/doc bodies before reasoning over them.
- Do not compress secrets, credentials, PATs, webhook URLs, raw private payloads, or files that must be inspected exactly for legal/security reasons. Inspect those locally and summarize public-safe conclusions.
- Keep `.codegraph/`, Headroom caches, and compression stats out of commits. Prefer `.git/info/exclude` or repo-local ignore rules when initializing indexes.
- When reporting progress in Multica, state whether CodeGraph was initialized/synced and whether Headroom/compact filtering was used for large outputs.

Recommended setup for a repo:

```powershell
vx codegraph status <repo>
vx codegraph init -i <repo>   # first time
vx codegraph sync <repo>      # after edits, branch changes, or stale index
```

## Single-Hop Mention Safety

Multica triggers every effective `mention://agent` or `mention://squad` in a newly created issue comment. A handoff comment must therefore contain only one live mention markdown: the current executor.

Use this format:

```markdown
[@小白](mention://agent/2db51e50-fae9-4b19-a4dc-c0b8b029d315) 触发原因：...
当前状态：...
需要你做：...
证据：...
NEXT_OWNER: loonghao
```

Do not write the future owner as a live mention in the same comment. For example, do not include `[@loonghao](mention://agent/...)` when the current task is for `小白`. The worker should create a new comment with the next live mention after finishing.

Routing tables are selection aids, not comment templates. If parallel work is required, create separate comments or separate issues, one live mention per comment.

If an agent is triggered only because it appeared as a future next owner, and the comment clearly says the current task is for another agent, the agent must no-op silently and must not add a “not for me” reply.

## GitHub Association Rules

If an issue, autopilot payload, comment, or user request contains a GitHub issue/PR URL, keep Multica and GitHub linked explicitly. Add or preserve a Multica association block with:

- `GitHub:` URL
- `Repo:` full repository name
- `Number:`
- `Type:` `issue` or `pr`
- `Labels:`
- `Milestone:`
- `GitHub assignees:`
- `Author:`
- `Linked GitHub issues:` for PRs
- `Routing signal:`
- `Multica next owner:`

Refresh GitHub state before routing:

```powershell
gh issue view <url> --json number,title,url,state,labels,assignees,author,body,comments,milestone
gh pr view <url> --json number,title,url,state,reviewDecision,statusCheckRollup,assignees,author,body,comments
gh pr checks <url>
```

GitHub assignees are routing hints, not Multica assignees. Keep unknown GitHub usernames visible in Multica comments and ask `loonghao` or `倩倩` to choose the Multica owner.

Use labels/components to route:

- docs / README / AGENTS / llms -> `小白`
- frontend / UI / web -> `dcc-mcp 前端/UI 小队` or `传林`
- backend / core / rust / go / python / protocol / API -> `dcc-mcp 后端/Core 小队`
- CI / release / GitHub Actions / branch protection -> `dcc-mcp CI/DevOps/Release 小队`
- test / e2e / flaky / coverage -> `dcc-mcp CI/DevOps/Release 小队` or `代码测试`
- product / spec / needs-triage -> `晓黎`
- docs / skills / release notes / public boundary -> `dcc-mcp Docs/Knowledge 小队`
- unclear ownership -> top-level `dcc-mcp 开发小组`, `爱写代码的小龙`, or `loonghao`

When CLI comments should trigger agents, use mention markdown, not plain text:

```markdown
[@loonghao](mention://agent/957463b6-e5c8-4d19-bc15-0be5b7e2133c)
```

Write GitHub comments only when explicitly needed for external/public communication. Any such comment must be concise English and public-safe. Do not expose Multica webhook URLs, trigger tokens, PATs, local paths, internal hostnames, private provenance, raw private payloads, Multica IDs, or agent routing. Do not use Chinese for GitHub public workflow/review/status comments.

Multica issue IDs and comments are internal-only. Do not put Multica issue IDs, Multica issue URLs, comment/task/autopilot/run IDs, internal short IDs, internal issue keys, agent routing history, or internal discussion excerpts into GitHub PR bodies, GitHub comments, reviews, commits, or release notes. In particular, never use `#123`, `fixes #123`, `closes #123`, or `resolves #123` for a Multica/internal issue; GitHub will treat it as a GitHub issue reference and may create wrong links or close the wrong issue. Use `fixes/closes/resolves #N` only after verifying `#N` with `gh issue view` in the target GitHub repo.

## Open PR Patrol And Squad Handoff

The self-loop autopilot should also scan open PRs across active `dcc-mcp` repositories:

```powershell
gh repo list dcc-mcp --limit 200 --json name,isArchived
gh pr list --repo dcc-mcp/<repo> --state open --json number,title,url,isDraft,mergeable,mergeStateStatus,reviewDecision,labels,assignees,author,updatedAt
gh pr checks <number> --repo dcc-mcp/<repo> --required --json name,bucket,state,link
```

The autopilot itself must not merge PRs. If a PR is open, non-draft, mergeable/clean or plausibly ready, and required checks are green, it should create or update a Multica tracking issue/comment for `loonghao` code-review, or route abnormal/pre-review work to the right specialized squad. Missing loonghao/code-review approval is a normal self-loop handoff, not a `needs-human` condition.

For `workflow_run` webhooks, do not rely only on `workflow_run.pull_requests`. Some repos run CI on `push`, so PR branch runs and post-merge default-branch runs can arrive with `pull_requests=[]`. Resolve PR association by calling `gh api -H "Accept: application/vnd.github+json" repos/<owner>/<repo>/commits/<head_sha>/pulls`, then by searching open PRs for a non-default `head_branch` and matching `headRefOid`. A default-branch success with only merged/closed PRs is `no_action_main_post_merge_success`; a default-branch failure is a CI/DevOps repo-health issue and must not be silently ignored.

Do not label same-repo/internal merge conflicts as `needs-human` on first sight. If live PR state is `mergeable=CONFLICTING`, `mergeable_state=dirty`, or `mergeStateStatus=DIRTY`, first route conflict recovery to the current implementer or Backend/Core squad: update the Multica issue with compact evidence, set `review_status=merge_conflict_required`, `pipeline_phase=implementation_feedback`, `merge_conflict_required=true`, status `in_progress`, then rerun or assign the owner. Use `needs-human` only after conflict recovery fails, permissions block the push, the branch belongs to an external contributor, release/product policy is ambiguous, or ownership cannot be routed. Also use it for failed/pending required checks after enough time, invalid public issue references, branch protection errors, security/privacy concerns, or unresolved review that automation cannot route. Leave GitHub public text only when an external/public answer is necessary, and keep it English/public-safe. Do not mention Multica issue IDs or internal tracking. Skip PRs already labeled `needs-human` until a human removes the label.

## Unassigned And Stale Issue Recovery

High `max_concurrent_tasks` only controls how many tasks an agent may run after work is enqueued. It does not assign, mention, rerun, or unstick issues by itself.

The hourly patrol must explicitly repair these states:

- It must not stop at report-only output when it finds real dcc-mcp PRs or issues that need routing. It should assign, mention, rerun, update status/metadata, or create a durable tracking issue. Demo/example repositories and Renovate/configure-only PRs may be ignored unless the user explicitly includes them.
- Active `todo` issue with no assignee: route it to the concrete first owner, a specialized dcc-mcp squad, or top-level `dcc-mcp 开发小组` when intake is still needed. For dcc-mcp/core/adapter/GitHub PR/CI issues, do not leave it unassigned after patrol.
- Active squad issue with no recent route comment: add one single-mention comment for the current next owner, or reassign to a concrete agent when exclusive ownership is clear.
- Stale `in_review` issue: verify whether it is waiting for loonghao/code-review, QA, product acceptance, CI green, or external human action. If it has a PR URL and CI is green but no current-head review request exists, trigger loonghao once. If CI failed/pending, route back to the fixer or keep implementer owner.
- Rejected PR review recovery: if the latest loonghao review/comment says request changes, not ready, 不足, 不能合并, needs fix, or lists blocking feedback, do not leave the issue in `in_review`. Route it back to one implementer/squad with a live mention or rerun current assignee, set `metadata.review_status=changes_requested`, and set status `todo` or `in_progress`.
- This applies to GitHub review comments and to plain Multica issue comments. A Multica comment without `mention://agent` is just a note; it does not enqueue the next agent.
- Intake `in_review` issue: if `metadata.pipeline_phase=intake_review`, check the intake-ready checklist. Promote to `todo` and assign only when implementation-ready; otherwise keep `in_review` and single-mention the missing intake owner.
- Stale `in_progress` issue: inspect `multica issue runs`; if there is no active run and no recent progress, rerun the current assignee or route to the correct owner.
- `waiting_local_directory`: fix project `local_directory` binding or reassign/comment to an agent/runtime that has the repo available. Concurrency cannot clear this state.
- `blocked`: only auto-route when the blocker is actionable by an agent. If it needs credentials, PyPI/GitHub settings, local DCC UI, or human approval, keep `blocked` and preserve `blocked_reason` / `waiting_on` metadata.

Suggested patrol thresholds:

- urgent/high: repair after 30 minutes of no progress.
- medium: repair after 2 hours.
- low/none, especially non-dcc/aether: keep low priority unless explicitly requested or parent issue says it is next.

When repairing, follow the safe order: comment evidence, set status, then reassign as the final mutation.

## PR CI Handoff Gate

For any task that creates, updates, force-pushes, or fixes a GitHub PR, the implementing agent owns the PR until the review handoff gate is satisfied.

Required checks before a live `loonghao` mention:

1. Refresh the PR with `gh pr view <pr> --repo <repo> --json number,title,url,state,isDraft,mergeStateStatus,reviewDecision,headRefOid,body`.
2. Check required CI with `gh pr checks <pr> --repo <repo> --required --json name,bucket,state,link`. If the repo has no required checks, inspect `statusCheckRollup` and state the fallback explicitly.
3. Treat `pending`, `queued`, `in_progress`, `waiting`, `neutral-but-not-final`, `cancelled`, `skipped unexpectedly`, `failed`, and missing required checks as not ready.
4. Inspect public PR text and commit metadata before handoff:
   - `gh pr view <pr> --repo <repo> --json body,title`
   - `gh api repos/<owner>/<repo>/pulls/<pr>/commits --jq '.[].commit.message'`
   - reject internal keys such as `PIP-123`, Multica issue IDs/URLs, routing history, local paths, or private provenance.
5. Only when PR is open, non-draft, mergeable/no conflict, public metadata is clean, and required checks are green may the agent post a Multica comment with a single live `loonghao` mention for code review.

While CI is pending:

- Do not post `已完成，请复核` with a live `loonghao` mention.
- Keep the Multica issue in progress. A plain progress comment without any live mention is allowed if the wait is long.
- Continue polling, or rely on the PR CI success autopilot/hourly patrol to re-check and trigger loonghao after the current head SHA is green.

When CI fails:

- Do not trigger loonghao for review.
- Fix the failure yourself if it is in scope, or publish one single-hop comment to the correct developer/tester with failing check links and the exact next action.
- The developer who fixes the failure repeats this gate from the new head SHA.

## Core Release Downstream Loop

Release-please publishes `dcc-mcp-core` releases/tags. Treat a published core release as the beginning of a downstream adapter iteration loop, not as the end of work.

Dedicated automation:

- Autopilot: `dcc-mcp-core release -> 下游专队迭代`
- ID: `5a5cc21e-bcfd-4dbd-bd14-ac2a3b73e164`
- Assignee: `dcc-mcp 开发小组`
- Mode: `run_only`; it must create/update compact durable Multica issues itself.
- Triggers: GitHub `release / published` from `dcc-mcp/dcc-mcp-core`, plus a schedule fallback every 30 minutes.
- Why fallback exists: GitHub `release.published` deliveries can be rate-limited (`429`) while later `release.edited` deliveries still succeed. The schedule scanner prevents downstream release trains from being missed.

When this loop runs:

1. Re-read recent releases with `gh release list --repo dcc-mcp/dcc-mcp-core --limit 10 --json tagName,name,isPrerelease,isDraft,publishedAt,createdAt`, then inspect affected tags with `gh release view <tag> --repo dcc-mcp/dcc-mcp-core --json tagName,name,isPrerelease,publishedAt,body`.
2. Dedupe by release tag/range before creating work. Search for `dcc-mcp-core <tag>`, release URL, and metadata such as `core_release_tag` / `core_release_latest_tag`.
3. If multiple unprocessed releases exist, create one release-train issue for the range, not one issue per tag.
4. Decide impact for downstream repos: `dcc-mcp-maya`, `dcc-mcp-blender`, `dcc-mcp-houdini`, `dcc-mcp-3dsmax`, `dcc-mcp-photoshop`, `dcc-mcp-unreal`, `dcc-mcp-zbrush`, `dcc-mcp-openusd`, and `dcc-mcp-fpt`.
5. For each repo, classify `PR`, `issue`, or `no_action` for dependency bumps, API/contract alignment, skill/docs updates, tests/CI, or downstream releases.
6. Route work through specialized squads, single-hop Multica comments, or child issues. Backend/API/contract work goes to Backend/Core; CI/release validation goes to CI/DevOps/Release; docs/skills/release notes goes to Docs/Knowledge; UI/web goes to Frontend/UI. Do not mention multiple future owners in one comment.
7. If downstream work exposes a core bug, missing migration path, unstable contract, or avoidable adapter burden, create a public-safe GitHub issue in `dcc-mcp/dcc-mcp-core` with `core-release-followup`; add `adapter-blocker` when it blocks adapter work.
8. Let the existing GitHub Issue sync autopilot bring that public core issue back into Multica, where the normal self-loop continues.

Hourly fallback:

- The self-loop patrol should check `gh release list --repo dcc-mcp/dcc-mcp-core --limit 1 --json tagName,name,url,isPrerelease,publishedAt`.
- If no active Multica issue contains the latest tag or release URL, run `multica autopilot trigger 5a5cc21e-bcfd-4dbd-bd14-ac2a3b73e164`.
- The release autopilot handles manual fallback by fetching the latest release itself.

## Renovate And Release-Please Gate

Do not turn every core release into manual downstream code work.

Classify downstream actions before creating child issues or PRs:

- `renovate_only`: only dependency constraints, lockfiles, generated install docs, or version references would change. Let Renovate/dependency automation handle it. Do not assign Backend/Core and do not create manual `core-<version>-align` PRs.
- `release_please_only`: release-please PRs, changelog, manifests, package version files, and generated release docs. Let CI success handoff route the PR to `loonghao` for review/merge.
- `watch_only`: additive core features that downstream repos do not currently consume and have no failing CI evidence. Record no_action/watch evidence only.
- `code_required`: breaking API/schema/contract/runtime behavior, downstream code consumes the changed contract, or a Renovate/release PR fails CI with evidence that adapter code must change. Only this class should create implementation issues.

Rules:

- A `dcc-mcp-core` version bump alone is not evidence of `code_required`.
- If a dependency-only PR is dirty or has no checks, do not route conflict recovery to developers. Mark the Multica issue `renovate_only` / `no_action_dependency_only`; add the public-safe `dependencies` label when useful; wait for Renovate or create a CI/DevOps issue to configure Renovate if missing.
- If a Renovate/dependency-only or release-please PR is green and clean, route to `loonghao` for review/merge through the normal PR CI success gate.
- If such a PR fails CI, route to CI/DevOps for failure classification first. Create developer work only when the failure proves code/API/schema changes are needed.

## Autopilot Operations

Prefer `create_issue` mode for workflows that need auditability.

```powershell
$description = Get-Content -Raw <prompt.md>
multica autopilot create --title "<title>" --description $description --agent <agent-id-or-name> --mode create_issue --priority <priority> --issue-title-template "<title {{date}}>" --output json
multica autopilot trigger-add <autopilot-id> --kind webhook --label "<label>" --output json
multica autopilot trigger-add <autopilot-id> --kind schedule --cron "0 9 * * 1-5" --timezone Asia/Shanghai --label "<label>" --output json
multica autopilot get <autopilot-id> --output json
multica autopilot runs <autopilot-id> --output json
```

Current CLI builds always accept agent IDs/names for `--agent`; some builds also accept squad IDs for existing squad-routed autopilots. If a squad update returns `assignee must be a valid agent in this workspace`, create/update with a temporary valid agent, then patch:

```powershell
$cfg = Get-Content -Raw "$env:USERPROFILE\.multica\config.json" | ConvertFrom-Json
$headers = @{ Authorization = "Bearer $($cfg.token)"; "X-Workspace-ID" = $cfg.workspace_id; "Content-Type" = "application/json" }
$body = @{ assignee_id = "<squad-id>"; assignee_type = "squad" } | ConvertTo-Json
Invoke-RestMethod -Method Patch -Uri "$($cfg.server_url.TrimEnd('/'))/api/autopilots/<autopilot-id>" -Headers $headers -Body $body
```

Webhook rules:

- Configure senders as `application/json`.
- Treat generated URLs as bearer secrets.
- Rotate leaked URLs immediately.
- Event filters match inferred event/action, not arbitrary body fields.
- No-op webhook responses are normally `200` with `ignored` or `skipped`; non-2xx means real delivery trouble.
- Watch for `429` per-token rate limit. Split noisy integrations across multiple triggers or repo-level hooks.

## Verification

Always finish with a concise verification block:

- Skill exists and files are attached.
- Agents/squad have the skill assigned.
- Instructions or squad roles were re-read after update.
- Webhooks/autopilots, if touched, have a passing ping or safe ignored delivery.
- Temporary files stayed in ignored workspace paths.
