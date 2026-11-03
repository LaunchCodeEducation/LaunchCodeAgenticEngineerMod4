# MarketRadar Agent Setup

## Docker Build

```bash
docker build -t marketradar-agent .
```

## Docker Run

```bash
docker run -it --rm \
  -v "$PWD":/workspace \
  -v claude-auth:/claude-auth \
  marketradar-agent
```

## Mounted Path

The only mounted host path is the project folder:

```
/workspace
```

This maps to my local `marketplace-tracker` directory.

## Network Mode

Default Docker bridge network.

## Smoke Test

Prompt used:

```
Summarize the repository structure and save the summary to /workspace/agent-summary.md
```

### Smoke Test Output

```text
❯ Summarize the repository structure and save the summary to /workspace/agent-summary.md.

Searched for 2 patterns, read 4 files, listed 1 directory.

● Write(agent-summary.md)
  ⎿ Wrote 49 lines to agent-summary.md

● Saved the summary to /workspace/agent-summary.md.

MarketRadar is a Facebook Marketplace tracker with two projects:
- tracker-api/ — Express + TypeScript + Prisma backend.
- tracker-client/ — React + Vite + Tailwind frontend.

ai-course:/workspace# ls
Dockerfile  agent-summary.md  tracker-api  tracker-client
```

## Security Decisions

### Why did I mount only this folder?

I only mounted my marketplace-tracker project because it’s the only folder Claude Code needed to access. This prevents the agent from reading or modifying unrelated files on my computer.

### What did I choose to keep ephemeral?

Temporary files, caches, and anything created outside /workspace stay inside the container and are removed when the container exits.

### What did I choose to persist?

I persisted my project files by mounting my marketplace-tracker folder to /workspace. I also persisted my Claude authentication using the claude-auth Docker volume.

### What dependencies did I include in my extended Docker image?

I included Node.js 20, npm, Git, Bash, Claude Code, ngrok, and the basic Linux utilities required to inspect, build, and work on this project.

### What did my smoke test prove?

The smoke test proved that Claude Code could safely work inside the container, create a file in /workspace, and that the file persisted to my local project because /workspace was a mounted volume.

### What risks remain?

The container still has network access, so an agent could make outbound requests if prompted. I also need to avoid mounting sensitive folders, secrets, production credentials, or API keys in the project.
## Module 3 MCP Network

Run the agent container on the `agent-internal` Docker network instead of `--network none`.

The internal bridge allows agents to communicate with MCP servers over localhost while still blocking external internet access.

```bash
docker network create --internal agent-internal
docker run --network agent-internal ...
Then verify exactly what we added:

```bash
tail -n 15 setup.md
