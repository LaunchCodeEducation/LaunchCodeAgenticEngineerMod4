# Module 4.2 — LaunchCode Agentic Engineer (CI/CD)

> **Note:** This repository covers **Module 4.2 (CI/CD) only.**
> For Module 4.1 and Module 4.3, use the materials in the main course repository:
> [https://github.com/jeffheaton/LaunchCodeAgenticEngineer/tree/main/module_4](https://github.com/jeffheaton/LaunchCodeAgenticEngineer/tree/main/module_4)

Docker development environment for LaunchCode's **Agentic Programming** course, Module 4.2 (CI/CD). Extends the Module 3 environment with:

- **Slack MCP server** — lets Claude Code prompts read and post to Slack
- **Gmail MCP server** — lets Claude Code prompts read and send email
- **Pre-configured skills** — custom slash commands available inside Claude Code
- **Pre-configured agents** — autonomous sub-agents Claude Code can invoke for specialized tasks
- **MarketRadar project** — the Module 3 Facebook Marketplace tracker and its evaluation harness, migrated in Module 4.1 (see [MarketRadar](#marketradar-migrated-from-module-3))

## Quick Start

Build and run locally:

```bash
cd module_4
docker build -t agentic_engineer_4 .
docker run -it --rm -p 8501:8501 -p 8502:8502 \
  -e SLACK_BOT_TOKEN=xoxb-your-token \
  -e SLACK_TEAM_ID=T0123456 \
  -v "$PWD":/workspace \
  agentic_engineer_4
```

Or pull the pre-built image from DockerHub:

```bash
docker run -it --rm -p 8501:8501 -p 8502:8502 \
  -e SLACK_BOT_TOKEN=xoxb-your-token \
  -e SLACK_TEAM_ID=T0123456 \
  -v "$PWD":/workspace \
  heatonresearch/agentic_engineer_4:latest
```

Full setup with Slack and Gmail (reads credentials from your shell environment):

```bash
docker run -it --rm \
  -p 8501:8501 -p 8502:8502 \
  -e ANTHROPIC_API_KEY=$ANTHROPIC_API_KEY \
  -e SLACK_BOT_TOKEN=$SLACK_BOT_TOKEN \
  -e SLACK_TEAM_ID=$SLACK_TEAM_ID \
  -v "$PWD":/workspace \
  -v "$HOME/.gmail-mcp":/root/.gmail-mcp \
  heatonresearch/agentic_engineer_4:latest
```

Place `credentials.json` (from Google Cloud Console) in `$PWD` before running. The Gmail MCP will trigger OAuth on first use and persist the token in `~/.gmail-mcp/`.

## MarketRadar (migrated from Module 3)

MarketRadar is a Facebook Marketplace tracker. It was migrated into this environment in Module 4.1. The original Module 3 README is preserved at [`docs/module3/README.md`](docs/module3/README.md).

| Path | Contents |
|---|---|
| `tracker-api/` | Express + TypeScript + Prisma backend |
| `tracker-client/` | React + Vite + Tailwind frontend |
| `.claude/agents/` | Module 3 subagents (`planner`, `implementer`, `tester`, `project-manager`, `marketradar-code-reviewer`) |
| `.memory/` | Layered project memory |
| `eval/module3/` | Module 3.3 evaluation harness and recorded evidence |
| `docs/module3/` | Module 3 documentation; see `migration-notes.md` for known issues |

**Requires Node.js >= 20.19** (Vite 8). The image build fails if the installed Node is older.

```bash
# Backend (Vitest suite; Prisma is mocked, no database needed)
cd tracker-api && npm ci && npm test

# Frontend
cd tracker-client && npm ci && npm run lint && npm run build

# Module 3 evaluation harness offline self-test (run from eval/module3)
cd eval/module3 && python3 -m unittest test_harness_selftest -v
```

## Build

```bash
docker build -t agentic_engineer_4 .
```

Force a complete rebuild (no cached layers):

```bash
docker build --no-cache -t agentic_engineer_4 .
```

## Run

### With a local workspace (recommended)

```bash
# macOS / Linux
docker run -it --rm -p 8501:8501 -p 8502:8502 \
  -e SLACK_BOT_TOKEN=xoxb-your-token \
  -e SLACK_TEAM_ID=T0123456 \
  -v "$PWD":/workspace \
  agentic_engineer_4

# Windows (PowerShell)
docker run -it --rm -p 8501:8501 -p 8502:8502 `
  -e SLACK_BOT_TOKEN=xoxb-your-token `
  -e SLACK_TEAM_ID=T0123456 `
  -v "${PWD}:/workspace" `
  agentic_engineer_4
```

Files created or edited inside `/workspace` are saved to your local folder and persist after the container exits.

### Without a local workspace

```bash
docker run -it --rm -p 8501:8501 agentic_engineer_4
```

Any files created inside the container will be lost when it exits.

---

## MCP Servers

MCP (Model Context Protocol) servers extend Claude Code so that prompts can take real-world actions — posting to Slack, reading email, etc. — without writing any extra code. Both servers are pre-installed as global npm packages and pre-configured in `/root/.claude/settings.json` inside the image.

### Slack MCP Server

**Package:** `@modelcontextprotocol/server-slack`

**Required environment variables** (pass with `-e` at `docker run`):

| Variable          | Description                                           |
| ----------------- | ----------------------------------------------------- |
| `SLACK_BOT_TOKEN` | Bot User OAuth Token from your Slack App (`xoxb-…`)   |
| `SLACK_TEAM_ID`   | Your Slack workspace ID (found in workspace settings) |

**Getting a Slack Bot Token:**

1. Go to [api.slack.com/apps](https://api.slack.com/apps) and create a new app.
2. Under **OAuth & Permissions**, add Bot Token Scopes: `channels:read`, `chat:write`, `channels:history`, `users:read`.
3. Install the app to your workspace and copy the **Bot User OAuth Token**.
4. Copy your workspace's **Team ID** from the workspace URL or settings.

**What it enables:** Claude Code prompts can list channels, read message history, post messages, and look up users in your Slack workspace.

### Gmail MCP Server

**Package:** `@gongrzhe/server-gmail-autoauth-mcp`

**Setup (OAuth):**

1. Go to [Google Cloud Console](https://console.cloud.google.com/) and create a project.
2. Enable the **Gmail API**.
3. Create OAuth 2.0 credentials (Desktop App type) and download `credentials.json`.
4. Place `credentials.json` in your workspace directory (mounted at `/workspace`).
5. On first use, the MCP server will open an OAuth flow and save a token. To persist the token across container restarts, mount the credentials directory:

```bash
docker run -it --rm -p 8501:8501 \
  -v "$PWD":/workspace \
  -v "$HOME/.gmail-mcp":/root/.gmail-mcp \
  agentic_engineer_4
```

**What it enables:** Claude Code prompts can read, search, and send Gmail messages on behalf of the authenticated user.

---

## Skills

Skills are custom slash commands invoked by typing `/skill-name` inside a Claude Code session. Claude Code supports two ways to define skills, and this image uses both.

### Pre-installed Skills

| Skill                 | Description                                                 |
| --------------------- | ----------------------------------------------------------- |
| `/send-slack-message` | Send a message to a Slack channel via the Slack MCP server  |
| `/check-gmail`        | Retrieve and summarize recent unread Gmail messages         |
| `/send-email`         | Draft and send an email via the Gmail MCP server            |
| `/summarize-session`  | Generate a bullet-point summary of the current work session |
| `/rebuild-and-deploy` | Rebuild the Docker image and push it to DockerHub           |

---

### SKILL.md files

Each skill lives in its own Markdown file at `.claude/skills/<skill-name>/SKILL.md`. Inside the container these are placed at `/root/.claude/skills/`.

```
skills/
  send-slack-message/SKILL.md
  check-gmail/SKILL.md
  send-email/SKILL.md
  summarize-session/SKILL.md
```

**When to use this method:**

- The skill prompt is more than a sentence or two.
- The skill has multiple steps, conditional logic, or examples that benefit from formatting.
- You want each skill in its own file for easier editing and version control.
- You are building skills that will be shared or maintained over time.

To add a skill, create a new directory and SKILL.md file:

```bash
mkdir -p skills/my-skill
cat > skills/my-skill/SKILL.md << 'EOF'
Description of what this skill does.

Steps:
1. First step Claude should take.
2. Second step.
3. Confirm result to the user.
EOF
```

Then rebuild the image so the file is copied into `/root/.claude/skills/`:

```bash
docker build -t agentic_engineer_4 .
```

**Adding a skill at runtime (no rebuild required):**

You can also add a skill directly inside a running container without rebuilding the image. The full path inside the container is:

```
/root/.claude/skills/<skill-name>/SKILL.md
```

For example:

```bash
mkdir -p /root/.claude/skills/my-skill
nano /root/.claude/skills/my-skill/SKILL.md
```

Note: since the container is run with `--rm`, any skills added this way will be lost when the container exits. To persist them, add them to the `skills/` directory in this repo and rebuild.

---

## Agents

Agents are autonomous sub-agents that Claude Code can spin up to handle specialized tasks. Unlike skills (which are slash commands you invoke), agents are specialists that Claude Code invokes automatically when the task matches, or that you can request explicitly in a prompt.

Agents are defined as Markdown files with YAML frontmatter and stored in `.claude/agents/` (inside the container: `/root/.claude/agents/`). Source files live in `agents/` in this repo and are copied in at image build time.

### Pre-installed Agents

| Agent           | Trigger description                                                                           |
| --------------- | --------------------------------------------------------------------------------------------- |
| `code-reviewer` | Reviews recent git changes for quality, security, and maintainability without modifying files |

### Running an Agent

**Explicitly — ask Claude Code to use it:**

```
Review my recent changes using the code-reviewer agent.
```

**Automatically** — Claude Code will invoke the agent on its own when the task matches the agent's description. For example, after you ask Claude to write a new feature, it may proactively run the code-reviewer agent.

### How the code-reviewer Agent Works

When invoked, `code-reviewer`:

1. Runs `git diff` to find recent changes.
2. Reads each modified file.
3. Classifies every issue as **Critical**, **Warning**, or **Suggestion**.
4. Provides a concrete fix example for every Critical and Warning item.

It checks for:

- Code clarity and naming conventions
- Duplicated logic
- Error handling and input validation
- Exposed secrets or API keys
- Test coverage for new behavior
- Performance implications

The agent never edits or creates files — it only reports.

### Adding a New Agent

1. Create a Markdown file in `agents/` with a YAML frontmatter block:

```markdown
---
name: my-agent
description: >
  One or two sentences describing when Claude Code should invoke this agent.
tools: Read, Grep, Glob, Bash
model: inherit
permissionMode: default
---

Your agent prompt goes here.
```

2. Rebuild the image:

```bash
docker build -t agentic_engineer_4 .
```

**Adding an agent at runtime (no rebuild required):**

```bash
mkdir -p /root/.claude/agents
nano /root/.claude/agents/my-agent.md
```

Note: agents added this way are lost when the container exits (since it runs with `--rm`). Add them to `agents/` in this repo and rebuild to persist them.

### Agent File Format

| Field            | Description                                                         |
| ---------------- | ------------------------------------------------------------------- |
| `name`           | Identifier used to reference the agent                              |
| `description`    | Tells Claude Code when to invoke the agent (be specific)            |
| `tools`          | Comma-separated list of tools the agent may use                     |
| `model`          | Model to use (`inherit` uses the same model as the parent session)  |
| `permissionMode` | `default` respects normal permission prompts; `allowAll` skips them |

---

## Running Subagent Containers

`scripts/run-agent.sh` (macOS/Linux) starts one role in its own container with the container permissions in `docs/governance-policy.md`, and `scripts/verify-container-permissions.sh` checks them on the Docker host. This applies only to containers started with the launcher: subagents started through Claude Code's Agent tool, the normal orchestration workflow, run inside the orchestrator's container and are not isolated. `scripts/run-agent.ps1` (Windows) has not been updated for Enforcement Layer 1. Pass the role name as the first argument; any additional arguments are forwarded to the container.

**macOS / Linux:**

```bash
# Read-only workspace, no memory mount (reviewer, tester, project-manager)
./scripts/run-agent.sh reviewer

# Read-write workspace, memory mounted (implementer, orchestrator)
./scripts/run-agent.sh implementer

# Pass a command to run inside the container
./scripts/run-agent.sh tester python3 -m pytest eval/ -v
```

**Windows (PowerShell):**

```powershell
# Read-only workspace, no memory mount
.\scripts\run-agent.ps1 reviewer

# Read-write workspace, memory mounted
.\scripts\run-agent.ps1 implementer

# Pass a command to run inside the container
.\scripts\run-agent.ps1 tester python3 -m pytest eval/ -v
```

Override the default image (`launchcode-agentic:module4`) with the `AGENT_IMAGE` environment variable:

```bash
AGENT_IMAGE=heatonresearch/agentic_engineer_4:latest ./scripts/run-agent.sh implementer
```

```powershell
$env:AGENT_IMAGE = 'heatonresearch/agentic_engineer_4:latest'
.\scripts\run-agent.ps1 implementer
```

---

## Gmail API Credentials (Python SDK)

In addition to the MCP server, the Python `google-api-python-client` library is available for direct API use in your code.

Place `credentials.json` (from Google Cloud Console) in your workspace directory. On first run it triggers OAuth and saves `token.json`. Reference it in code as:

```python
from google_auth_oauthlib.flow import InstalledAppFlow

flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
```

Keep both files out of source control:

```
# .gitignore
credentials.json
token.json
```

---

## Running Streamlit Apps

From inside the container:

```bash
streamlit run app.py
```

Then open [http://localhost:8501](http://localhost:8501) in your browser.

---

## Running Unit Tests

The test suite runs inside the Docker container, which has all dependencies pre-installed. Build the image first if you haven't already:

```bash
docker build -t agentic_engineer_4 .
```

### Run all eval tests

```bash
docker run --rm \
  -v "$PWD":/workspace \
  agentic_engineer_4 \
  python3 -m pytest eval/ -v
```

### Run specific test suites

```bash
# Deterministic router and handoff-validator unit tests (fast, no external deps)
docker run --rm -v "$PWD":/workspace agentic_engineer_4 \
  python3 -m pytest eval/test_deterministic_router.py eval/test_deterministic_step.py -v

# Full deterministic suite including CLI subprocess and directory-structure checks
docker run --rm -v "$PWD":/workspace agentic_engineer_4 \
  python3 -m pytest eval/test_deterministic.py -v

# Governance policy / allow-list / skill-scope enforcement tests
docker run --rm -v "$PWD":/workspace agentic_engineer_4 \
  python3 -m pytest eval/test_policy.py -v

# Rubric suite placeholders
docker run --rm -v "$PWD":/workspace agentic_engineer_4 \
  python3 -m pytest eval/test_rubric_suite.py -v
```

### What each suite checks

| Suite | What it tests |
| --- | --- |
| `test_deterministic_router.py` | `scripts/route_task_deterministic.py` path-to-role routing logic |
| `test_deterministic_step.py` | `scripts/validate_handoff_deterministic.py` field validation logic |
| `test_deterministic.py` | CLI invocation of the validator, directory structure, governance-policy content |
| `test_policy.py` | Governance and CI files exist and the CI policy gate is not advisory; MCP storage and retrieval allow-list authorization, the retrieval classification ceiling and the storage store default; the `run-tests` skill Activation Scope, which agents hold the Skill tool, the skill-scope hook's decisions; container permissions from `scripts/run-agent.sh` (run with a fake docker); and the required fields of the audit records written for storage, retrieval and skill-scope denials and for retrieval withholding. Expected values are hard-coded from `docs/governance-policy.md`. These are deterministic tests; they do not start Claude Code or Docker. |
| `test_rubric_suite.py` | Rubric/judge placeholders — confirms ADR and CI design docs contain required content |

### Notes

- `eval/test_policy.py` checks the `run-tests` skill scope from `.claude/skills/run-tests/SKILL.md`. It does not read `.skills/*.md`, which is still empty, or check the scope of other skills.
- Tests that check directory structure (`.agents`, `.skills`, `docs/adr`, etc.) expect those directories to exist in the bind-mounted workspace. They are created automatically when the container runs without a bind-mount.
- `scripts/run-reviewer.py` is a safe sample that does **not** call a live LLM. It writes a deterministic advisory review so the CI workflow can be exercised without API spend.
- Containers started with `scripts/run-agent.sh` write runtime logs to the `agent-logs` Docker volume, mounted at `/logs`, not to the repository. `logs/` is not gitignored.
- Configure branch protection so `Policy Test Suite`, `Evaluation Harness`, and `Pipeline Integrity Check` are required status checks before merge.

---

## Build & Deploy to DockerHub

This section covers the full workflow for building the image and publishing it to DockerHub so students can pull it without building locally.

### Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed and running
- A DockerHub account (free at [hub.docker.com](https://hub.docker.com))
- Logged in to DockerHub on your machine:

```bash
docker login
```

### Step 1 — Build and tag for DockerHub

Build the image and tag it with your DockerHub username and repository name. Replace `heatonresearch` with your DockerHub username if different.

```bash
cd module_4
docker build -t heatonresearch/agentic_engineer_4:latest .
```

To tag a specific version number alongside `latest` (recommended so students can pin to a known-good version):

```bash
docker build \
  -t heatonresearch/agentic_engineer_4:latest \
  -t heatonresearch/agentic_engineer_4:3.0 .
```

Force a full rebuild ignoring all cached layers:

```bash
docker build --no-cache \
  -t heatonresearch/agentic_engineer_4:latest \
  -t heatonresearch/agentic_engineer_4:3.0 .
```

### Step 2 — Push to DockerHub

```bash
docker push heatonresearch/agentic_engineer_4:latest
docker push heatonresearch/agentic_engineer_4:3.0
```

Both tags must be pushed separately. The `latest` tag is what students get by default when they don't specify a version.

### Step 3 — Verify the image is public

Visit `https://hub.docker.com/r/heatonresearch/agentic_engineer_4` and confirm the repository visibility is set to **Public** so students can pull without logging in.

### Pulling the image (students)

Once published, students can run the image directly without cloning the repo or building anything:

```bash
docker run -it --rm -p 8501:8501 -p 8502:8502 \
  -e SLACK_BOT_TOKEN=xoxb-your-token \
  -e SLACK_TEAM_ID=T0123456 \
  -v "$PWD":/workspace \
  heatonresearch/agentic_engineer_4:latest
```
