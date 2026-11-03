# MarketRadar Routing and Tool-Grant Map

| Role | Receives from Orchestrator | Produces | Tools Granted | Tools Denied | Context Isolation Reason | Autonomy |
|---|---|---|---|---|---|---|
| Planner | Task, acceptance criteria, repository context | Implementation plan and explicit file list | Read, Grep, Glob | Edit, Write, Bash | Planning should not change code or execute commands | High within planning scope |
| Implementer | Approved plan, file list, acceptance criteria | Code changes and implementation summary | Read, Grep, Glob, Edit, Write | Test execution and unrelated tools | Implementation is limited to the approved plan | Medium |
| Tester | Acceptance criteria, implementation summary, modified files | PASS/FAIL verification report | Read, Grep, Glob, Bash | Edit, Write | Testing must remain independent from implementation | High within verification scope |
| Orchestrator | Task plus outputs from each role | Routing decisions, approvals, retries, escalation | Delegation and evaluation only | Specialized implementation work | Coordinates specialists instead of doing their work | High for routing |
 
## Routing

1. Orchestrator sends the task to Planner.
2. Planner returns a plan and explicit file list.
3. Human approves the plan.
4. Orchestrator sends the approved plan to Implementer.
5. Implementer makes the approved changes and returns a summary.
6. Orchestrator sends the implementation to Tester.
7. Tester returns PASS or FAIL.
8. On PASS, the workflow completes.
9. On FAIL, the Orchestrator routes the findings back to Implementer.
10. After changes, Tester verifies again.
11. Repeated failure is escalated to the human.
