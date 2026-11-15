# Step Classification: FashionMate Agentic Harness

Author: swarna. Date: 2026-11-14.

**How this document is maintained.** This document is updated after every calibration cycle. Steps that cross the stability threshold are promoted to candidate status. A step that has been a candidate for more than two calibration cycles without meeting all four signals is reviewed for re-scoping: either it moves back to the agent column as judgment work, or its scope is narrowed until it can stabilize. Every agent-classified step carries a specific next-review date, and any step is re-checked early after a major workflow change. Last updated: 2026-11-15 (citation list assembly conversion recorded, ADR-003).
Source of the step list: `docs/orchestration-diagram.md` (walked from the parent outward), `eval/orchestrator.py`, `.claude/agents/`, and the CI pipeline in `.github/workflows/ci.yml`.

**Method.** Every step is tested against the four signals: stability, repeatability, specifiability, high run rate. Evidence comes from the Module 3 calibration log (`docs/calibration-log.md`), the Module 4 calibration log, and a read-only analysis of the committed run transcripts (30 with role outputs) in `.eval-artifacts/runs/` (`scripts/analyze_citations.py`, no model calls). Those transcripts were produced by `eval/orchestrator.py` inside the course container during calibration, so the behavior measured is the behavior that would be converted.

**Summary.** 15 steps listed. As of 2026-11-15: 8 agentic, 7 deterministic (citation list assembly converted under ADR-003). Open candidates: 2 weak (tester, project manager); 6 not candidates. Original audit (2026-11-14): 9 agentic, 6 deterministic, 1 strong candidate.

| # | Step | Kind today | Recommendation |
|---|---|---|---|
| 1 | Orchestrator sequencing (role order, loop/skip/escalate) | Deterministic code in `run_orchestrator` | Already deterministic |
| 2 | File-path routing to a role | Deterministic (`test_deterministic_router.py`, 5 tests) | Already deterministic |
| 3 | Scoped handoff construction (`handoff = next_handoff`) | Deterministic (fix d02de14) | Already deterministic |
| 4 | Handoff / output schema validation | Deterministic (`test_deterministic_step.py`, `output_schema` check) | Already deterministic |
| 5 | Reviewer-conflict escalation | Deterministic (fix a5e0643) | Already deterministic |
| 6 | Retrieval similarity floor + keyword fallback | Deterministic (fix ecb7e5f) | Already deterministic |
| 7 | Citation list assembly (each role's `citation_list`) | Deterministic (`scripts/assemble_citations.py`, ADR-003) | **Converted 2026-11-15** |
| 8 | Tester (run tests, report pass/fail) | Agentic | Weak candidate |
| 9 | Project manager (update ticket status) | Agentic | Weak candidate |
| 10 | Planner | Agentic | Not a candidate |
| 11 | Implementer | Agentic | Not a candidate |
| 12 | Reviewer (incl. strict/lenient pair) | Agentic | Not a candidate |
| 13 | Researcher (optional stretch) | Agentic | Not a candidate |
| 14 | Advisory code review (CI) | Agentic | Not a candidate |
| 15 | Rubric judge (agent-as-judge) | Agentic | Not a candidate |

---

## Step: Citation list assembly (each role's `citation_list`)

- **Status: Converted to deterministic (ADR-003, 2026-11-15).** `scripts/assemble_citations.py`, called by `eval/orchestrator.py` after each role finishes (PR #13). Decision and evidence: `docs/adr/ADR-003-citation-list-deterministic-conversion.md`; before/after measurements and the end-to-end regression check (0 regressions) in `docs/calibration-log.md`.
- **Preserved edge cases:** a role with no `retrieve` call gets `[]` (inherited upstream citations are not copied); storage entry IDs are never cited; rows whose `source_document` is missing, non-string, or blank/whitespace-only are skipped rather than guessed at. All covered by `eval/test_citation_assembly.py` (20 tests, part of the CI deterministic gate).
- **Next review:** none as an agent step. Re-open only if the `retrieve` result format changes or an `inherited_citations` field is requested (out of scope per ADR-003).

The assessment below is the original classification (2026-11-14), kept as the record of why the step was converted.

What it does today: every role is told in `_FINALIZE_INSTRUCTIONS` (eval/orchestrator.py, line 385): *"For roles using retrieve, list the source_document names in citation_list."* The model writes the list itself.

- **Stability:** the task definition has not changed since the Module 3 schema fix (2e31057), and its failure modes are now fully catalogued. The harness's `output_schema` check passed on every development run after 2e31057 (six reruns, 14/14 each, plus REGRESSION-default) and on all 6 measured holdout tasks, across two calibration cycles (2026-11-05 baseline, 2026-11-07 calibration). Note: that check confirms the field *exists*, not that its contents are *correct*; correctness was measured separately below.
- **Repeatability:** the deterministic rule (Rule A, below) is a pure function of the role's own `retrieve` results in the transcript: the same tool calls always give the same list. The agent's list did not consistently follow its own tool calls. Measured on the default development task, the same input run 7 times during calibration (RUN-20261105-020424, -024607, -052236, RUN-20261107-002930, -014242, -060001, REGRESSION-default):

  | Role | Runs | Distinct lists the agent wrote | Distinct lists its own retrievals justify (Rule A) |
  |---|---|---|---|
  | planner | 7 | 1 | 1 |
  | implementer | 7 | 4 | 2 |
  | reviewer | 6 | 2 | 2 |
  | tester | 7 | 5 | 1 |

  The planner (which always retrieves) matched the rule every time. The implementer and tester varied more than their own tool calls justify: the tester retrieved nothing in all 7 runs (Rule A gives `[]` every time) yet wrote 5 different lists.
  Across all 30 transcripts with role outputs (122 outputs), the agent matched Rule A exactly in **84 (68.9%)**. The other 38: 12 (9.8%) same documents in a different order; 9 (7.4%) cited storage entry IDs instead of documents; 8 (6.6%) cited real documents although the role made no `retrieve` call; 5 (4.1%) used paraphrased or invented names (e.g. "Incident Report" for `incident-report-2024-q3.md`); 4 (3.3%) had no `citation_list` at all. For comparison, a rule that also inherits the previous role's citations (Rule B) matched only 59 (48.4%), so "carrying citations forward" is not what the agent consistently did.
  Conclusion: the *correct output* is fully repeatable from the transcript; the *agent* reproduces it reliably only when it has a real lookup to do. The variation is a spec violation, not useful judgment.
- **Specifiability:** one-paragraph spec (Rule A), written so a developer could implement it without questions: *For each role's output, `citation_list` is the list of `source_document` values from that role's own `retrieve` tool results in the current run, deduplicated, in order of first appearance. If the role made no `retrieve` calls, it is `[]`. Results withheld by the classification ceiling are never returned by `retrieve`, so they cannot appear. The model no longer writes this field; the orchestrator sets it after the role finishes, overwriting anything the model produced.*
- **Run rate:** runs on every role output in every orchestrator run: 4 per standard run, 5 on the five-role path, and on every holdout and regression run. Many times per day during development and every CI evaluation.
- **Known agent judgment / edge-case input the deterministic version must preserve:** a role that did **not** call `retrieve` but built on documents passed down in its handoff (implementer, tester, reviewer). The agent *sometimes* carried the planner's citations forward (8 outputs cited real documents with no `retrieve` call), which looks like provenance-tracking judgment, but it did so inconsistently (the "own + inherited" Rule B matched only 48.4%). The deterministic version must make this explicit rather than lose it silently: `citation_list` = own retrievals only (matching the written spec), and upstream provenance stays available through the scoped handoff chain. A second edge case: a role that read **storage entries** (`read_entry`) and cited their IDs. Storage entries are not documents, so the deterministic version does not list them; this is a deliberate change from the agent's occasional behavior and is recorded in the ADR.
- **Original recommendation (2026-11-14): strong candidate.** All four signals are met, the correct output is a lookup over data the orchestrator already holds, and converting it removes one of the six Module 3 failure modes (schema validation) by design instead of by prompt wording.

## Step: Tester (run tests, report pass/fail)

- **Stability:** behavior well understood in the four-role path; passed `required_roles` and `role_order` on every run after 45ccef5.
- **Repeatability:** not yet measurable for its core output. In the harness the tester does not run a real test suite, so there is no pass/fail result to compare across runs; its citation output varied (5 distinct lists in 7 runs where its own retrievals justify 1).
- **Specifiability:** yes in principle: run pytest on the changed files, report exit code and pass/fail counts.
- **Run rate:** every standard run.
- **Edge case to preserve:** pytest exit code 5 ("no tests collected"). An agent can report "no tests apply to this change"; a naive script would treat it as a failure or a pass.
- **Recommendation: weak candidate.** To qualify: give the tester a real test-runner tool in the harness and complete two calibration cycles comparing its reported result to the actual pytest exit code.
- **Candidate since:** 2026-11-14. **Next review:** 2026-12-15 (near: a weak candidate that could qualify once it has a real test-runner tool and two calibration cycles).

## Step: Project manager (update ticket status)

**Readiness review: 2026-11-15 (Module 4 exercise).** Conversion-readiness package for this step: the classification below, the proposed decision in `docs/adr/ADR-004-project-manager-ticket-status-deterministic-conversion.md` (Status: Proposed), and the test, measurement and rollback plan at the end of this section. Nothing has been built or measured for a replacement.

**What it does.** The project manager is the terminal role of the full workflow (`.claude/agents/project-manager.md`, v1.1.0). It receives the parent orchestrator's assembled run summary (ticket ID, what was implemented, review outcome, test outcome, and any status the parent wants recorded), chooses the ticket status (`Done`, `Needs Work`, `Blocked`, or a status the parent specifies), updates the ticket with `mcp__coursetools__task_tracker` and adds a short note, then returns a fixed-format confirmation to the parent. Governance requires a human checkpoint before the ticket update (`docs/governance-policy.md`, orchestrator autonomy conditions); that checkpoint sits outside this step and stays whichever way the step is implemented.

| Signal | Score | Evidence |
|---|---|---|
| Stability | Fail | The task definition itself is not settled. The agent file describes the project manager as the *last* role, which updates a ticket; the eval harness defines it as the *first* role, which must "create a project entry in the store" (`eval/orchestrator.py`, `_ROLE_DESCRIPTIONS["project_manager"]`), while governance denies it `write_entry` (`docs/governance-policy.md`, role project-manager). The agent file itself changed between runs (v1.0.0 to v1.1.0, after Iteration Log Misfire 1). The only harness run of the five-role path, HO-07, crashed at step 1 because the project manager called `write_entry` without `project_id` (`docs/calibration-log.md`, "Remaining gaps"). |
| Repeatability | Not measured (fail) | There are no same-input repetitions. The step has completed end to end exactly once (`docs/iteration-log.md`, Run 1, 2026-11-03: ticket CSV-EXPORT-1 set to `Done` after human confirmation), plus one project-manager-only rerun (`docs/iteration-log.md`, Rerun 2026-11-04). None of the 38 committed JSON artifacts under `.eval-artifacts/` contains a project-manager event, so no replay over past runs is possible. |
| Specifiability | Pass for the status decision; partial for the note | The status guidance in the agent file is already a decision table: implemented, review passed and all tests passed gives `Done`; review or tests failed gives `Needs Work`, `Blocked` or the parent's status; an ambiguous summary gives no update and an open question; a tracker error is reported exactly. Only the free-text note needs wording, and a template ("review passed, tests 12/12") would satisfy the agent's required output format. |
| Run rate | Low (fail) | Once per run, and only on the five-role path. No development or holdout task measured in the two calibration cycles includes the project manager except HO-07, which crashed; the step has run once in a live session (Iteration Log Run 1). |

**Known agent judgment / edge-case input:** an incomplete or ambiguous run summary, above all a summary with **no ticket identifier**. In Iteration Log Run 1 (2026-11-03, Misfire 1) the project manager received no ticket ID; it did not invent one or update another ticket, it stopped, and the human supplied `CSV-EXPORT-1` mid-run. The same judgment covers the related cases the agent file names ("If the parent's summary is ambiguous, do not guess"): a test outcome that is only an aggregate PASS with no per-test detail (Iteration Log Misfire 6), and a run escalated to a human after a reviewer conflict (fix a5e0643), which must never be recorded as `Done`. A deterministic version must return "no update, open question" for these inputs every time instead of mapping them to the nearest status.

**Recommendation: weak candidate.** The status decision is specifiable, close to a lookup table, so the step is a plausible future conversion. It fails stability, repeatability and run rate: its definition differs between the agent file and the harness, it has completed only once, and it runs on a path that two calibration cycles never measured. Converting now would mean encoding a decision table that has never been compared with what the agent actually does, for a step that almost never runs, so the expected savings are small and the evidence is missing. It stays agentic until the harness definition matches the agent file, the HO-07 crash is fixed, and the five-role path has run for two calibration cycles.
- **Candidate since:** 2026-11-14. **Next review:** 2026-12-15 (near: re-check after the HO-07 crash is fixed and the five-role path completes two calibration cycles).

### Conversion plan (for use only if the step reaches strong-candidate status)

Proposed replacement (ADR-004): `scripts/ticket_status.py` with a pure function `decide_ticket_update(summary)` that returns either `{"action": "update", "ticket", "status", "note"}` or `{"action": "ask", "question"}`. The orchestrator would call it where it now invokes the project-manager agent, keep the human checkpoint before the update, and make the `task_tracker` call itself.

**Test plan** (`eval/test_ticket_status.py`, no model calls):

| # | Test | Input | Expected output | Why it matters |
|---|---|---|---|---|
| 1 | Normal success | Ticket `CSV-EXPORT-1`, implemented, review passed, tests 12/12 with per-test results | `update`, status `Done`, note "review passed, tests 12/12" | Reproduces the one completed live run (Iteration Log Run 1). |
| 2 | Failure case | Same ticket, review passed, tests 10/12 with two named failures | `update`, status `Needs Work`, note names both failing tests; never `Done` | A failing run must never close a ticket. |
| 3 | Tracker error | Valid input; the tracker returns an error | No retry; the error is reported to the parent exactly; `Update performed: no` | Agent file rule: report the error exactly and do not attempt unrelated workarounds. |
| 4 | **Named edge case: missing ticket ID** | Review passed, tests 12/12, `ticket` absent, empty, or whitespace-only | `ask` with "No ticket identifier in the run summary"; **no tracker call** | Iteration Log Misfire 1. A script that defaulted or guessed would update the wrong ticket, or none, on every such run, silently. |
| 5 | Edge case: aggregate-only test result | Ticket present, review passed, test outcome "PASS" with no per-test counts | `ask`, no update | Iteration Log Misfire 6; the agent file says an ambiguous summary must not be guessed. |
| 6 | Edge case: escalated run | Tests 12/12, review passed, `escalated_to_human: true` | Never `Done`; `Blocked` with note "escalated to human" | The reviewer-conflict escalation (a5e0643) must carry through to the ticket. |
| 7 | Parent-specified status | Parent requests a status outside the allowed set (for example `On Hold`) | `ask`; a requested status inside the set is used as given | Prevents an unknown status being written to the tracker. |

**Measurement plan.** A baseline must be collected first, because none exists. After the harness project manager is made to match the agent file and HO-07 is fixed, run the five-role path for two calibration cycles (HO-07 plus one five-role development task, 3 runs each on the same input) and record, for every project-manager invocation, the status chosen, whether it asked a question, latency and tokens. Then run the same inputs through the script.
- **Latency:** project-manager invocation time versus script time.
- **Token cost:** agent tokens per invocation versus 0. Prerequisite: fix the bug where `token_count` is never added to `total_tokens` (`docs/calibration-log.md`: "Cost check is vacuous"); otherwise both sides read 0 and the comparison means nothing.
- **Predictability:** distinct statuses across 3 same-input runs (agent) versus 1 (script), and the agreement rate between the agent's choice and the decision table on every recorded summary. Every disagreement is reviewed one by one before acceptance, because each is either an agent error or a rule the table is missing.
- **Audit clarity:** the tracker audit entry records which rule fired (for example `rule: tests_failed`) instead of a free-text rationale.
- **Quality and harness:** HO-07 assertions (all five roles in order, budgets), `required_roles`, `role_order`, policy suite 40/40, deterministic gate unchanged; end to end on HO-07 plus two development tasks with 0 regressions.
- **Rubric:** clarity and groundedness of the project manager's note become not applicable for a templated note and are marked N/A, not scored 0, so a lower rubric total is not misread as a regression. Correctness and task_adherence still apply.

**Rollback note.** The conversion would land as one focused commit, in its own PR with nothing unrelated in it, containing: `scripts/ticket_status.py` and `eval/test_ticket_status.py`; the orchestrator change that calls the function instead of the project-manager agent (role description and invocation); the project-manager row in `docs/routing-and-tool-grant-map.md` and `.json` changed to a deterministic step holding only `task_tracker`; the project-manager role entry in `docs/governance-policy.md` plus a line under "Deterministic conversion history"; `.claude/agents/project-manager.md` marked retired (moved, not deleted); the role list in `eval/test_policy.py`, which asserts that project-manager exists; and the CI deterministic-gate step adding the new test file. If the replacement failed after integration, `git revert <that commit>` restores the agent definition, its prompt, the map row, the policy entry, the policy test and the CI line together. The human checkpoint before the ticket update is unchanged in both directions, so a rollback never removes a safeguard.

## Step: Planner

- **Stability:** rubric scores low and variable (part of 38/80 aggregate on holdout).
- **Repeatability:** plans differ in wording and structure between runs, which is expected for open-ended planning.
- **Specifiability:** no. Producing an ordered plan from a free-text feature request requires judgment.
- **Run rate:** every run.
- **Edge case:** not applicable (not converting).
- **Recommendation: not a candidate.** Its retrieval-citation sub-task is covered by step 7.
- **Next review:** 2027-02-15 (distant: open-ended planning is judgment work and unlikely to become specifiable soon).

## Step: Implementer

- **Stability / repeatability:** code output varies by design.
- **Specifiability:** no. Writing code to a plan is judgment work.
- **Run rate:** every run.
- **Recommendation: not a candidate.**
- **Next review:** 2027-02-15 (distant: writing code to a plan stays judgment work).

## Step: Reviewer (and the strict/lenient pair)

- **Stability:** the Module 3 conflict cycle showed verdicts depend heavily on prompt framing.
- **Specifiability:** no. Judging code quality has contested criteria.
- **Run rate:** every run.
- **Recommendation: not a candidate.** (The conflict *resolution* is already deterministic, step 5.)
- **Next review:** 2027-02-15 (distant: contested quality criteria).

## Step: Researcher (optional stretch)

- **Specifiability:** no. Open-ended external documentation questions.
- **Run rate:** rare (only on a research blocker).
- **Recommendation: not a candidate.**
- **Next review:** 2027-05-15 (distant and low priority: rare run rate).

## Step: Advisory code review (CI)

- **Stability:** measured false-positive rate 29% (PR #1), 38% (PR #4), about 50% (PR #5).
- **Specifiability:** no. Open-ended review.
- **Run rate:** every pull request.
- **Recommendation: not a candidate.** It stays agentic and advisory (see `docs/ci-step-design.md`).
- **Next review:** 2027-02-15 (distant: re-check the false-positive rate in the calibration log before then).

## Step: Rubric judge

- **Specifiability:** no. Scores correctness, adherence, groundedness and clarity.
- **Stability:** judge-bias risk noted in Module 3 (loads project CLAUDE.md).
- **Recommendation: not a candidate.**
- **Next review:** 2027-02-15 (distant: scoring prose quality needs judgment).

---

## Already deterministic (listed to keep the picture honest)

Orchestrator sequencing, file-path routing, scoped handoff construction, handoff/output schema validation, reviewer-conflict escalation, the retrieval similarity floor with keyword fallback, and (since ADR-003, 2026-11-15) citation list assembly are plain code with deterministic tests. The target state is a mixed workflow: judgment steps stay agentic, rule steps are code, and humans review escalations.

## Reproducing the evidence

```
python scripts/analyze_citations.py .
```

Reads only the committed transcripts; prints the match rates, the difference categories, and the repeatability counts above. Every figure is measured against Rule A unless labelled Rule B, and the script exits non-zero if it finds no transcripts.

**Evidence correction (2026-11-14).** The first version of this analysis mixed Rule A and Rule B in its difference categories and claimed the implementer and reviewer "never call retrieve". The advisory code review on the classification PR flagged the inconsistency; the script was fixed to measure everything against Rule A, and the figures above are the corrected ones. The recommendation did not change.
