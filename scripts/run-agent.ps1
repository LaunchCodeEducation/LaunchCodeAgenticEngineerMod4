# run-agent.ps1: launch a subagent container with only the permissions its
# governance policy allows. Pass the role name as the first argument.
#
# Usage: .\scripts\run-agent.ps1 <role-name> [command...]
# Roles: implementer, orchestrator, planner, reviewer, tester, project-manager
# Permissions follow docs/governance-policy.md: deny first (read-only, no memory),
# then widen only for roles whose policy entry requires it.

param(
    [Parameter(Mandatory = $true, Position = 0)]
    [string]$Role,

    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$ExtraArgs
)

$ErrorActionPreference = 'Stop'

$Image = if ($env:AGENT_IMAGE) { $env:AGENT_IMAGE } else { 'agentic_engineer_4' }
$WorkspaceMode = 'ro'
$MountMemory = $false

switch ($Role) {
    { $_ -in 'implementer', 'orchestrator' } {
        $WorkspaceMode = 'rw'
        $MountMemory = $true
    }
    # planner: plans from retrieved docs, writes no project files (policy: autonomy low)
    { $_ -in 'planner', 'reviewer', 'tester', 'project-manager' } {
        $WorkspaceMode = 'ro'
        $MountMemory = $false
    }
    default {
        Write-Error "Unknown role: $Role"
        Write-Error "This role has no policy entry, so it cannot be launched."
        exit 1
    }
}

# Convert backslashes so Docker volume paths work correctly on Windows.
$CurDir = (Get-Location).Path -replace '\\', '/'
New-Item -ItemType Directory -Force -Path 'logs' | Out-Null

$DockerArgs = @(
    'run', '--rm', '-it',
    '--network', 'agent-internal',
    '-v', "${CurDir}:/workspace:${WorkspaceMode}",
    '-v', "${CurDir}/logs:/logs:rw",
    '-e', 'STORAGE_AUDIT_LOG=/logs/storage-audit-log.jsonl',
    '-e', 'RETRIEVAL_AUDIT_LOG=/logs/retrieval-audit-log.jsonl',
    # Pass the API key through from the host shell without echoing its value.
    '-e', 'OPENROUTER_API_KEY',
    '-e', 'SLACK_BOT_TOKEN=', '-e', 'SLACK_TEAM_ID=',
    # Claude Code login persistence (not project state).
    '-v', 'claude-auth:/claude-auth'
)

if ($MountMemory) {
    $DockerArgs += '-v', 'agent-memory:/memory'
}

$DockerArgs += '-e', "AGENT_ROLE=$Role"
$DockerArgs += $Image

if ($ExtraArgs) {
    $DockerArgs += $ExtraArgs
}

$MemoryState = if ($MountMemory) { 'mounted' } else { 'omitted' }
Write-Host "Launching '$Role': workspace=$WorkspaceMode, memory=$MemoryState"

& docker $DockerArgs
