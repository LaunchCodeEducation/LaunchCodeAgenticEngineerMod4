# run-agent.ps1: launch a subagent container with only the permissions its
# governance policy allows. Pass the role name as the first argument.
#
# Usage: .\scripts\run-agent.ps1 <role-name> [command...]
# Roles: implementer, orchestrator, reviewer, tester, project-manager, documentation-writer
param(
    [Parameter(Mandatory = $true, Position = 0)]
    [string]$Role,

    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$ExtraArgs
)

$ErrorActionPreference = 'Stop'

$Image = if ($env:AGENT_IMAGE) { $env:AGENT_IMAGE } else { 'agentic_engineer_4:latest' }
$WorkspaceMode = 'ro'
$MountMemory = $false

switch ($Role) {
    { $_ -in 'implementer', 'orchestrator' } {
        $WorkspaceMode = 'rw'
        $MountMemory = $true
    }
    { $_ -in 'reviewer', 'tester', 'project-manager', 'documentation-writer' } 
{
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
    '-e', 'RETRIEVAL_AUDIT_LOG=/logs/retrieval-audit-log.jsonl'
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
