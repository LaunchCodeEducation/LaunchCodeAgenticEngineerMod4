# MarketRadar Orchestration Diagram

## Workflow Task

Prevent a saved search from accepting a negative maximum price.

## Workflow

```text
                         +----------------+
                         |  Orchestrator  |
                         +-------+--------+
                                 |
                    task + repository context
                                 |
                                 v
                         +-------+--------+
                         |    Planner     |
                         +-------+--------+
                                 |
                       plan + file list
                                 |
                                 v
                    [Human approves plan]
                                 |
                                 v
                         +-------+--------+
                         |  Implementer   |
                         +-------+--------+
                                 |
                         modified files
                                 |
                                 v
                         +-------+--------+
                         |     Tester     |
                         +-------+--------+
                                 |
                        pass/fail report
                                 |
                                 v
                         +-------+--------+
                         |  Orchestrator  |
                         +----------------+

## Role Boundaries

- **Planner:** reads and searches the codebase to produce an implementation plan. It cannot modify files or run tests.
- **Implementer:** modifies the files required by the approved plan. It does not evaluate its own work with the test runner.
- **Tester:** runs the relevant tests and reports pass or fail. It cannot modify source code to make a failing test pass.
- **Orchestrator:** routes work between roles, evaluates each result, and handles human checkpoints. It does not perform the specialized work itself.

## Evaluation and Failure Routing

1. The Planner returns a plan and explicit file list.
2. A human approves the plan before implementation begins.
3. The Implementer makes only the approved changes.
4. The Tester verifies the behavior.
5. If testing fails, the Orchestrator routes the failure back to the Implementer.
6. After another implementation attempt, the Tester runs again.
7. If repeated attempts cannot satisfy the acceptance criteria, the Orchestrator stops and escalates to the human.

## Role Boundaries

- **Planner:** reads and searches the codebase to produce an implementation plan. It cannot modify files or run tests.
- **Implementer:** modifies the files required by the approved plan. It does not evaluate its own work with the test runner.
- **Tester:** runs the relevant tests and reports pass or fail. It cannot modify source code to make a failing test pass.
- **Orchestrator:** routes work between roles, evaluates each result, and handles human checkpoints. It does not perform the specialized work itself.

## Evaluation and Failure Routing

1. The Planner returns a plan and explicit file list.
2. A human approves the plan before implementation begins.
3. The Implementer makes only the approved changes.
4. The Tester verifies the behavior.
5. If testing fails, the Orchestrator routes the failure back to the Implementer.
6. After another implementation attempt, the Tester runs again.
7. If repeated attempts cannot satisfy the acceptance criteria, the Orchestrator stops and escalates to the human.
