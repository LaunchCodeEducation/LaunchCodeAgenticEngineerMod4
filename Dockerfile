FROM python:3.12-slim

WORKDIR /workspace

# --- Environment variables ---
# Prevent .pyc files and enable unbuffered output for cleaner container logs
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    # HuggingFace / Sentence Transformers cache inside the workspace so it
    # persists across container runs when /workspace is bind-mounted.
    # These dirs are created below; if /workspace is bind-mounted the host
    # directory will shadow them, but HF will re-create subdirs as needed.
    HF_HOME=/workspace/.cache/huggingface \
    SENTENCE_TRANSFORMERS_HOME=/workspace/.cache/sentence-transformers

# --- OS packages ---
# Core tools (curl, git, etc.) plus Module 4.2 diagnostics/build dependencies:
#   build-essential / python3-dev  — compile Python packages with C extensions
#   sqlite3                        — inspect SQLite DBs used by storage MCP server
#   jq                             — parse/pretty-print JSON from MCP responses
#   unzip / less / tree            — general file inspection
#   iproute2 / net-tools / lsof    — inspect listening ports and network state
#   dnsutils                       — DNS lookup inside the container
#   make                           — run Makefiles in lesson starter kits
RUN apt-get update && apt-get install -y \
    curl \
    git \
    bash \
    ca-certificates \
    nano \
    procps \
    nodejs \
    npm \
    gettext-base \
    build-essential \
    python3-dev \
    sqlite3 \
    jq \
    unzip \
    less \
    tree \
    iproute2 \
    net-tools \
    lsof \
    dnsutils \
    make \
    && rm -rf /var/lib/apt/lists/*

# --- Python packages ---
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Verify critical Module 4.2 imports so the build fails fast on a bad package
# rather than surprising students at runtime.
RUN python3 -c "\
import fastmcp; \
import mcp; \
import aiosqlite; \
import chromadb; \
import sentence_transformers; \
import sklearn; \
import pydantic; \
import httpx; \
import rank_bm25; \
print('All Module 4.2 imports OK')"

# --- Node/npm agent tooling ---
# Claude Code is the primary agent harness for this course.
RUN npm install -g @anthropic-ai/claude-code

# OpenCode is supported as an alternative harness.
RUN npm install -g opencode-ai

# MCP servers for Slack and Gmail integrations.
RUN npm install -g @modelcontextprotocol/server-slack
RUN npm install -g @gongrzhe/server-gmail-autoauth-mcp

# Verify Node tooling versions (non-fatal for version flags, fatal for missing binaries).
RUN node --version && \
    npm --version && \
    (claude --version 2>/dev/null || claude version 2>/dev/null || echo "claude installed (no --version flag)") && \
    (opencode --version 2>/dev/null || opencode version 2>/dev/null || echo "opencode installed (no --version flag)")

# --- ngrok ---
RUN curl -sSL https://ngrok-agent.s3.amazonaws.com/ngrok.asc \
    | tee /etc/apt/trusted.gpg.d/ngrok.asc >/dev/null \
    && echo "deb https://ngrok-agent.s3.amazonaws.com buster main" \
    | tee /etc/apt/sources.list.d/ngrok.list \
    && apt-get update && apt-get install -y ngrok \
    && rm -rf /var/lib/apt/lists/*

# --- Claude Code configuration ---
RUN mkdir -p /root/.claude/skills
COPY skills/ /root/.claude/skills/

RUN mkdir -p /root/.claude/agents
COPY agents/ /root/.claude/agents/

# --- Module 4 workspace content ---
# Copy source files into the image so the environment works without a bind-mount.
# When /workspace is bind-mounted at runtime these are shadowed by the host files,
# which is fine — the host copy wins and students edit it directly.
COPY mcp-servers/ /workspace/mcp-servers/
COPY scripts/ /workspace/scripts/
COPY docs/ /workspace/docs/
COPY eval/ /workspace/eval/
COPY schemas/ /workspace/schemas/
COPY examples/ /workspace/examples/
COPY CLAUDE.md /workspace/CLAUDE.md

# --- Workspace directory structure for Module 4 ---
# /workspace itself is typically bind-mounted, so these dirs may be shadowed
# at runtime. Creating them here ensures they exist in the image-only case
# and documents the expected layout for the lesson.
#
# .agents / .skills  — per-role governance scope files (eval/test_policy.py reads these)
# docs/adr           — Architecture Decision Records checked by eval tests
# logs               — runtime audit logs from storage/retrieval MCP servers
# .memory/reference  — persistent agent memory mount point
# Note: when running subagents via scripts/run-agent.sh the default image tag
#       is launchcode-agentic:module4 (set AGENT_IMAGE to override).
RUN mkdir -p \
    /workspace/mcp-servers/storage \
    /workspace/mcp-servers/retrieval \
    /workspace/.agents \
    /workspace/.skills \
    /workspace/.memory/reference \
    /workspace/.cache/huggingface \
    /workspace/.cache/sentence-transformers \
    /workspace/docs/adr \
    /workspace/eval \
    /workspace/scripts \
    /workspace/schemas \
    /workspace/examples \
    /workspace/logs \
    /workspace/tests

# --- Entrypoint ---
COPY docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

# --- Shell quality-of-life for learners ---
RUN echo 'export PS1="ai-course:\w# "' >> /root/.bashrc && \
    echo 'alias ll="ls -alF"' >> /root/.bashrc && \
    echo 'alias la="ls -A"' >> /root/.bashrc && \
    echo 'alias l="ls -CF"' >> /root/.bashrc && \
    echo 'alias python="python3"' >> /root/.bashrc && \
    echo 'alias py="python3"' >> /root/.bashrc && \
    echo 'alias pip="pip3"' >> /root/.bashrc && \
    echo 'alias ports="lsof -i -P -n"' >> /root/.bashrc && \
    echo 'alias mcp-servers="find /workspace/mcp-servers -maxdepth 3 -type f | sort"' >> /root/.bashrc

ENTRYPOINT ["docker-entrypoint.sh"]
CMD ["/bin/bash"]
