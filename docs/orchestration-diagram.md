# Orchestration Diagram - CSV Export Workflow

This file uses Mermaid because GitHub and GitLab can render Mermaid diagrams directly inside Markdown.

```mermaid
graph TD
    P[Parent / Orchestrator<br/>Sequences work, evaluates outputs, and decides when to loop, skip, or escalate]
    PL[Planner<br/>Produces an ordered plan and file list]
    IM[Implementer<br/>Writes code according to the plan]
    RV[Reviewer<br/>Read-only review of proposed changes]
    TS[Tester<br/>Runs tests and reports pass/fail]
    PM[Project Manager<br/>Updates the ticket status]
    RS[Researcher<br/>Optional stretch: answers external documentation questions]

    P -->|Feature request + repo path| PL
    PL -->|Plan document + file list| P

    P -->|Plan + file list| IM
    IM -->|Modified files| P

    P -->|Modified files| RV
    RV -->|Review report| P

    P -->|Modified files| TS
    TS -->|Test results| P

    P -->|Assembled run summary| PM
    PM -->|Ticket update confirmation| P

    IM -->|Research blocker, if needed| P
    P -->|Single research question| RS
    RS -->|Findings document| P
    P -->|Findings as added input| IM
```

## Handoff summary

1. The parent invokes the `planner` with the feature request and repository path.
2. The parent sends the resulting plan and file list to the `implementer`.
3. The parent sends modified files to the `reviewer`.
4. The parent sends modified files to the `tester`.
5. The parent sends the assembled run summary to the `project-manager`.
6. In the optional stretch flow, the parent invokes the `researcher` only when another role raises an external-documentation blocker.
