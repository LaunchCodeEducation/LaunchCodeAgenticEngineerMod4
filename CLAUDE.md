# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

This is a Docker-based development environment for LaunchCode's **Agentic Programming** course, Module 4.

This fork carries the **FashionMate** agentic harness forward from Modules 1–3
(target codebase: `swarnaburra/Unit-2-Project-Fashion-Mate`, a Spring Boot backend
plus React frontend). Project artifacts brought forward:

- Orchestrator and subagents: `.claude/agents/` (orchestrator, planner, implementer,
  reviewer, tester, project-manager) and `agents/`
- Evaluation harness: `eval/orchestrator.py`, `eval/rubric.json`, `eval/run_holdout.py`,
  locked holdout set in `docs/holdout-task-set.md`, evidence in `.eval-artifacts/runs/`
- Calibration record: `docs/calibration-log.md`; routing and grants:
  `docs/routing-and-tool-grant-map.md` / `.json`
- Memory and handoff templates: `.memory/knowledge/`, reference corpus `.memory/reference/`
- Course tools MCP server: `mcp/coursetools_server.py` (registered in `.mcp.json`)

Module 4 adds governance (`docs/governance-policy.md`, `eval/test_policy.py`), CI/CD
(`.github/workflows/ci.yml`, `scripts/`), and deterministic validation/routing
(`schemas/handoff.json`, `scripts/*_deterministic.py`).

## Docker Commands

Build the image:
```bash
docker build -t agentic_engineer_4 .
```

Force a clean rebuild:
```bash
docker build --no-cache -t agentic_engineer_4 .
```

Run with a local workspace mounted (recommended):
```bash
docker run -it --rm -p 8501:8501 -p 8502:8502 \
  -e SLACK_BOT_TOKEN=your-token \
  -e SLACK_TEAM_ID=your-team-id \
  -v "$PWD":/workspace \
  agentic_engineer_4
```

Pull and run the pre-built image from DockerHub:
```bash
docker run -it --rm -p 8501:8501 -v "$PWD":/workspace heatonresearch/agentic_engineer_4:latest
```

## MCP Servers

Two MCP servers are pre-installed and configured in `/root/.claude/settings.json`:

### Slack
- Package: `@modelcontextprotocol/server-slack`
- Requires env vars: `SLACK_BOT_TOKEN`, `SLACK_TEAM_ID`
- Allows Claude Code prompts to read channels, post messages, and interact with Slack workspaces.

### Gmail
- Package: `@gongrzhe/server-gmail-autoauth-mcp`
- OAuth credentials stored in `/root/.gmail-mcp/` (persist this directory across container runs if needed)
- Allows Claude Code prompts to read, search, and send Gmail messages.

## Skills

Pre-configured skills (invoked with `/skill-name` in Claude Code):

| Skill | Description |
|---|---|
| `/send-slack-message` | Send a message to a Slack channel |
| `/check-gmail` | Summarize recent unread Gmail messages |
| `/send-email` | Draft and send an email via Gmail |
| `/summarize-session` | Bullet-point summary of the current session |
| `/rebuild-and-deploy` | Rebuild the Docker image and push it to DockerHub |

Skills are defined in `settings.json` which is copied to `/root/.claude/settings.json` during image build.

## Agents

Pre-configured sub-agents available inside Claude Code sessions. Agents are autonomous specialists that Claude Code can invoke automatically or that you can request explicitly.

| Agent | Description |
|---|---|
| `code-reviewer` | Reviews recent git changes for quality, security, and maintainability |
| `email-summarize` | Checks new Gmail messages and posts sender + 2-line summary to #test Slack channel |

Agents are defined as Markdown files with YAML frontmatter in `/root/.claude/agents/` inside the container. Source files live in the `agents/` directory of this repo and are copied in at build time.

**Running an agent:**

Ask Claude Code to use the agent explicitly:
```
Review my recent changes using the code-reviewer agent.
```

Or Claude Code may invoke it automatically when the task matches the agent's description.

## Running Streamlit Apps

From inside the container:
```bash
streamlit run app.py
```

Access at `http://localhost:8501`.

## Key Dependencies (requirements.txt)

- `anthropic` — Claude API client
- `streamlit` — web UI framework
- `python-dotenv` — environment variable management
- `slack_sdk` — Slack integration (Python)
- `google-api-python-client`, `google-auth-oauthlib` — Gmail/Google API access (Python)
- `fastapi`, `flask`, `uvicorn` — web frameworks
- `pydantic`, `httpx` — HTTP and data validation

## Environment & Tools in the Container

- Python 3.12 (aliased as `python` and `pip`)
- Claude Code CLI (`claude`) installed globally via npm
- OpenCode (`opencode-ai`) installed globally via npm
- MCP server: `@modelcontextprotocol/server-slack`
- MCP server: `@gongrzhe/server-gmail-autoauth-mcp`
- ngrok for tunneling
- Workspace mounted at `/workspace`

## Gmail API Setup

Place `credentials.json` (from Google Cloud Console) in your workspace directory. On first run it triggers OAuth and saves `token.json`. Both files should be in `.gitignore`.

## Orchestrator workflow instructions

You are the Orchestrator for the CSV-export workflow. You do not write code,
run tests, search the web, or update tickets. Your job is to decompose the
task, delegate each piece to the right subagent, judge each result, and
assemble the final output. If you are ever about to do a subagent's work, stop
and invoke that subagent instead. Write files only for handoff briefs and the
final summary, never for source code.

Allowed tools: Agent (to invoke subagents), mcp__coursetools__file_read,
mcp__coursetools__file_write (handoff briefs and final summary only).
Denied tools: mcp__coursetools__codebase_search, mcp__coursetools__shell,
mcp__coursetools__test_runner, mcp__coursetools__task_tracker,
mcp__coursetools__web_search.

### Workflow goal and acceptance criteria
Goal: add a working "export tasks to CSV" feature, as specified in the PRD at
docs/prd.md. The full run is accepted only when all of the following hold:
- the feature behaves as the PRD describes,
- the Reviewer reports no unresolved high-severity issues, and
- the Tester reports all tests passing.

### Standard sequence
Invoke the subagents in this order, passing the named input to each:
1. planner          receives: feature request + repo path
2. implementer      receives: plan + file list
3. reviewer         receives: modified files
4. tester           receives: modified files
5. project-manager  receives: assembled run summary + ticket ID (from the "Ticket:" line in docs/prd.md)

Use the handoff templates in .memory/knowledge/ for every brief and result.

### Evaluation gate
After each subagent returns, check its result against that phase's acceptance
criteria BEFORE invoking the next role. Pass forward only a result that meets
the criteria. If it does not, apply the branching logic below.

### Branching logic
- Loop: if the Reviewer reports more than three issues, loop back to the
  implementer with the review report as input, then re-run the reviewer.
- Loop: if the Tester reports any failing test, loop back to the implementer
  with the failures as input, then re-run the tester.
- Skip: if the plan states "no code change required," skip the implementer and
  go straight to the reviewer.
- Halt and escalate: if the same phase fails its gate twice in a row, stop and
  escalate to the human with a short summary of what failed.

### Human-in-the-loop checkpoints
- After the planner: pause and show the plan to the human for approval before
  any code is written.
- Before the project-manager updates the ticket: pause for human confirmation,
  since changing the shared ticket is a consequential, outward-facing action.

### Output
Write a final summary (what was built, review outcome, test outcome, ticket
status) to docs/run-summary.md.
