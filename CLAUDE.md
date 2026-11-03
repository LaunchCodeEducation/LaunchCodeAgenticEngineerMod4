# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

This is a Docker-based development environment for LaunchCode's **Agentic Programming** course, Module 4.

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

---

## MarketRadar Project (migrated from Module 3)

MarketRadar is a Facebook Marketplace tracker, migrated into this Module 4 environment in Module 4.1.

| Path | Contents |
|---|---|
| `tracker-api/` | Express 5 + TypeScript + Prisma backend (Vitest tests in `tracker-api/tests/`) |
| `tracker-client/` | React 19 + Vite 8 + Tailwind 4 frontend (requires Node.js >= 20.19) |
| `.claude/agents/` | Module 3 project subagents: `planner`, `implementer`, `tester`, `project-manager`, `marketradar-code-reviewer` |
| `.memory/` | Layered project memory (project / knowledge / reference) |
| `mcp/` | Module 3 storage/retrieval MCP servers — reference only, not wired into Module 4 |
| `eval/module3/` | Module 3.3 evaluation harness, rubrics and recorded evidence |
| `docs/module3/` | Module 3 documentation (PRD, API, calibration log, reflection, etc.) |
| `docs/module3/migration-notes.md` | Migration record and known Module 3 failures |

**Precedence:** Module 4 governance (`docs/governance-policy.md`, `mcp-servers/*/allow-list.json`, `scripts/run-agent.sh`, `.github/workflows/ci.yml`) is authoritative. Where the Module 3 rules below conflict with it, Module 4 wins.

The Module 3 `code-reviewer` subagent was renamed `marketradar-code-reviewer` so it does not override the image-level `code-reviewer` agent.


### Memory Configuration

#### Layer 1: Project Memory

Location: `.memory/project/`

Stores project-specific decisions, current feature state, unresolved issues, and deliberately deferred work.

Claude may create and update project memory when significant project state or decisions change.

#### Layer 2: Knowledge Files

Location: `.memory/knowledge/`

Stores stable, human-maintained rules such as coding standards, architecture rules, API conventions, and security requirements.

Knowledge files are read-only for Claude. Claude must not create, modify, or delete these files.

#### Layer 3: Indexed Reference Documents

Location: `.memory/reference/`

Stores longer background material that is useful occasionally but should not be loaded into every session.

Claude should retrieve only the reference documents relevant to the current task.

#### Memory Policies

- At the start of a session, read `.memory/SCOPE.md` and `.memory/project/MEMORY_INDEX.md`.
- Verify that `.memory/SCOPE.md` matches the current project before using project memory.
- Do not use memory belonging to another project or repository.
- Treat source code, tests, configuration, and current documentation as authoritative when memory conflicts with the repository.
- Treat stale or conflicting memory as needing review rather than silently relying on it.
- Never store credentials, authentication tokens, cookies, secrets, personal data, or transient debugging output in memory.
- Claude may write to project memory but must not write to `.memory/knowledge/` or `.memory/reference/`.

#### Data Classification Before Writing

Before writing anything to any memory layer, classify it first:

- Public: may be written to appropriate memory.
- Internal: only store in a non-committed location.
- Confidential: do not write to agent memory; retrieve from the secure source when needed.
- Secret: never write to any memory layer. Use only for the immediate task and reference environment-variable names instead of values.
- If a secret is already found in memory, flag it and stop until a human removes/remediates it.

#### Knowledge File Permission Policy

Never modify file permissions in `.memory/knowledge/` without explicit human instruction. If a write fails because the knowledge directory is read-only, stop and ask the human rather than changing permissions.

#### Required Session Startup

Before responding to the user's first task in every new Claude Code session:

1. Read `.memory/SCOPE.md` and verify it matches the current repository.
2. Read `.memory/project/MEMORY_INDEX.md`.
3. Read every active Project Memory entry listed in the index.
4. Read active Knowledge Files listed in the index.
5. Complete these memory reads before responding to the user's request.

Do not wait for the user to explicitly ask you to load project memory.

### Orchestrator Workflow

For orchestrated development tasks, coordinate the specialized subagents rather than performing their work yourself.

#### Standard Sequence

1. Send the task and acceptance criteria to the Planner.
2. Require the Planner to return a plan and explicit file list.
3. Stop for human approval before implementation.
4. After approval, send the approved plan to the Implementer.
5. Require the Implementer to stay within the approved scope.
6. Send the completed implementation and acceptance criteria to the Tester.
7. Require the Tester to return PASS or FAIL with evidence.
8. If testing passes, report completion.
9. If testing fails, route the Tester findings back to the Implementer.
10. After fixes, send the implementation back to the Tester.
11. If repeated attempts cannot satisfy the acceptance criteria, stop and escalate to the human.

#### Handoff Rules

Use the templates in:

- `.memory/knowledge/handoff-orchestrator-to-subagent.md`
- `.memory/knowledge/handoff-subagent-to-orchestrator.md`

Pass only the context required by the receiving role.

#### Role Boundaries

- Planner plans but does not modify code or run tests.
- Implementer modifies code only within the approved plan.
- Tester verifies behavior but does not modify source code.
- Orchestrator coordinates, evaluates, routes, and escalates rather than performing specialized work.

#### Human Checkpoints

Human approval is required after the Planner phase and before implementation begins.

#### Evaluation Gate

A task is complete only when the Tester reports PASS against the acceptance criteria.

A FAIL must be routed back to the Implementer rather than fixed by the Tester or Orchestrator.
