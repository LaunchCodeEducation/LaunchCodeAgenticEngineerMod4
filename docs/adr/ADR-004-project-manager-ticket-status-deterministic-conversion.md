# ADR-004: Convert the project manager's ticket-status decision from agent to deterministic code

## Status
Proposed

(Numbered 004 because ADR-001, ADR-002 and ADR-003 already exist in `docs/adr/`.)

## Context

The project manager is the terminal role of the full workflow (`.claude/agents/project-manager.md`, v1.1.0). From the parent orchestrator's run summary it chooses a ticket status, updates the ticket with `mcp__coursetools__task_tracker`, adds a short note, and returns a fixed-format confirmation. Its status guidance is already written as rules: implemented, review passed and all tests passed gives `Done`; review or tests failed gives `Needs Work`, `Blocked` or the parent's status; an ambiguous summary gives no update and an open question; a tracker error is reported exactly. That makes the status decision look like a lookup, which is why `docs/step-classification.md` lists it as a candidate.

The readiness review of 2026-11-15 classifies it as a **weak candidate**, not a strong one. Specifiability passes for the status decision, but the other three signals fail. Stability: the step is defined two ways, as a terminal ticket updater in the agent file and as an opening "create a project entry" role in `eval/orchestrator.py`, while governance denies the project manager `write_entry`; the one harness run of the five-role path (HO-07) crashed at step 1 when the project manager called `write_entry` without `project_id` (`docs/calibration-log.md`). Repeatability: there are no same-input runs; the step has completed once (`docs/iteration-log.md`, Run 1, 2026-11-03) plus one project-manager-only rerun (2026-11-04), and none of the 38 committed JSON artifacts contains a project-manager event. Run rate: once per run, only on the five-role path, which the two calibration cycles never completed.

The judgment the agent applies today, which any replacement must keep, is refusing to act on an incomplete or ambiguous summary. Iteration Log Run 1, Misfire 1: no ticket ID reached the project manager, it stopped instead of guessing, and the human supplied `CSV-EXPORT-1` mid-run. Related cases: an aggregate-only test PASS with no per-test detail (Misfire 6), and a run escalated to a human after a reviewer conflict (fix a5e0643), which must never be recorded as `Done`.

Related records: ADR-001, ADR-002 and ADR-003 moved three structural steps to code once they met all four signals. This ADR records the same decision for a step that does not yet meet them, so the reasoning exists before any code does.

## Decision

Proposed, and not to be implemented yet: once the readiness conditions in `docs/step-classification.md` are met, replace the project manager agent's status decision with a pure function, `decide_ticket_update(summary)` in `scripts/ticket_status.py`. It returns either an update (ticket, status from the agent file's rules, templated note) or an open question, and it returns the open question whenever the ticket ID is missing or blank, the test outcome is aggregate-only or missing, or the parent requests a status outside the allowed set; an escalated run is never `Done`. The orchestrator calls it in place of the agent, keeps the human checkpoint before the update, and makes the `task_tracker` call itself. Until the conditions are met, the agent stays.

## Alternatives considered

- **Keep the agent (status quo).** Preferred for now. The step runs rarely, the human checkpoint already stands between the agent's choice and the ticket, and there is no measured case of the agent choosing a wrong status. Converting before there is a baseline would replace an unmeasured agent with an unmeasured script.
- **Tighten the prompt or require structured output.** Not chosen on its own. The status guidance is already explicit and the output format is already fixed; the failures seen so far (missing ticket ID, the HO-07 crash) came from the inputs and the harness definition, not from vague wording, so more prompt wording would not fix them.
- **Keep the agent and add a deterministic guardrail.** A small check that blocks any update without a ticket ID and blocks `Done` when tests failed or the run was escalated. Viable as an interim safeguard, and worth adding even if the step is never converted. It is not the long-term answer: the guardrail would already compute most of the decision table, so once the table is proven, keeping a model to reproduce it adds cost without benefit.
- **Partial conversion: code decides the status, the agent writes the note.** Rejected. The note is short and its content is fixed by the summary; keeping a model only for one sentence keeps model cost, latency and governance overhead for little value.
- **Full conversion to deterministic code.** Proposed for when the conditions are met, for the reasons in Decision.

## Consequences

Expected, not measured: the same summary always gives the same status; the audit entry records which rule fired instead of a free-text rationale; the step's latency and token cost drop to near zero; and "ticket updated with no ID" becomes impossible by construction.

Trade-offs: the script loses the agent's ability to read nuance in an unstructured summary. Any summary shape not in the table becomes an open question, which may increase human interruptions; that is acceptable because a checkpoint already exists at this point. A wrong rule would be wrong every time, not occasionally, so acceptance depends on comparing the agent's real choices with the table before switching. The conversion also needs the orchestrator to pass a structured summary (fields, not prose), which is a change to the handoff and must be part of the same commit.

Before this ADR can move to Accepted: reconcile the harness role definition with the agent file; fix the HO-07 crash; complete two calibration cycles on the five-role path; and then meet the test, measurement and rollback plan in `docs/step-classification.md`.

## Evidence

Available now (all committed):
- Classification and recommendation: `docs/step-classification.md`, "Step: Project manager (update ticket status)", commit 50010e1.
- Agent definition: `.claude/agents/project-manager.md` (status guidance, ambiguity rule, output format).
- Harness definition that differs: `eval/orchestrator.py`, `_ROLE_DESCRIPTIONS["project_manager"]`; grant: `docs/governance-policy.md`, role project-manager (`write_entry` denied).
- HO-07 crash: `docs/calibration-log.md`, "Remaining gaps".
- The only completed runs and the edge case: `docs/iteration-log.md`, Run 1 (2026-11-03, Misfires 1 and 6) and the project-manager-only rerun (2026-11-04).

To gather before acceptance (none of this exists yet, and no figures are claimed here):
- Baseline: every project-manager invocation over two calibration cycles of the five-role path (status chosen, question asked or not, latency, tokens), with 3 same-input runs per task.
- Agreement between the agent's chosen status and the decision table on every recorded summary, with each disagreement explained.
- After conversion: the unit tests in the test plan, same-input repeatability, latency and token cost, HO-07 and the end-to-end regression check with 0 regressions, and the policy suite.

Pressure test (raised as a teammate would in review): "Convert it now. The rules are already written in the agent file, both failures we have seen (the missing ticket ID and the HO-07 crash) were the agent's, and the human checkpoint makes a bad status cheap to catch. Because the step runs so rarely, waiting for two calibration cycles means waiting indefinitely, and a weak candidate that never gets evidence just stays weak." The disagreement is settled by evidence, not argument: (1) the agreement rate between the agent's choices and the decision table over at least six five-role runs, which shows whether the table is complete or whether the agent is applying judgment the table lacks; and (2) how often summaries actually arrive incomplete or ambiguous, which shows whether "ask" would be rare or would interrupt the human on most runs. Both are listed above as evidence to gather.
