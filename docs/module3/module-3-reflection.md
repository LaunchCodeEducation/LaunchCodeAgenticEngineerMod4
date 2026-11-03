# Module 3 Lab Reflection: Run a Full Calibration Cycle

All figures come from `docs/calibration-log.md` and the reports under `eval/evidence/calibration/`.

## 1. What evidence shows the root cause rather than just the symptom? How did the deterministic checks and the rubric scoring each help?

The **symptom** was that the Tester returned a lint summary without having run lint. The **root cause** was the tool configuration. Three pieces of evidence point to the cause rather than the symptom:

- **Tool-grant evidence.** In the before-fix run, `tool_authorization` recorded the grants `['Read', 'Grep', 'Glob', 'mcp__retrieval__retrieve']`, with no Bash. The global CLI permissions did not add Bash back. This is a property of the configuration, not of the agent's reasoning.
- **Tool-call evidence.** `lint_command_evidence` found 0 lint Bash calls. Instead, the Tester made 12 Read, Glob and Grep calls, which shows it was working around a missing capability rather than misreading the lint output.
- **Ruling out other layers.** `routing_order` and `real_transcript_present` passed in both runs, so routing and transcript capture were not at fault. After Bash was restored, and with nothing else changed, the two failing checks flipped to PASS in `CAL-AFTER-001`. Changing only that one variable is what ties the failure to the grant.

**Deterministic checks** found and located the fault. Each check maps to one failure mode, so the pattern of results (the grant and lint-evidence checks failing, the routing and transcript checks passing) narrowed the cause to tool configuration. **Rubric scoring** contributed only once the deterministic gate passed. The gate blocked scoring for the before-fix and after-fix runs, which both exceeded the 40,000-token limit. Scoring did run for `CAL-REGRESSION-001`, which got 12/12 rubric points across 3 dimensions and confirmed that, once lint could run, the summary was accurate and actionable. Scoring the before-fix output would have measured the quality of a summary of lint that never ran, which is why the gate comes first.

## 2. Why was the fix applied to the Tester's tool grants rather than another orchestration layer?

- **That layer was where the fault was.** The before-fix transcript shows the restriction came from the Tester's agent definition (`.claude/agents/tester.md`). The CLI `--allowedTools` flag did not override it. Changing routing, prompts or the orchestrator would have treated the symptom and left the Tester unable to run its own validation commands.
- **It was the smallest change that matched the role.** The Tester's job is to "run the tests or validation commands relevant to the task", which needs Bash. Restoring one tool kept everything else unchanged, including `permissionMode: plan`, the read-only rules, and the absence of Write and Edit. The `no_source_writes` check still passed after the fix.
- **It kept the change narrow.** Raising thresholds, changing the harness, or widening grants for other roles would have hidden the problem or weakened the evaluation. None of those were changed.

The holdouts show the tool-grant layer still has open problems. Retrieval was denied by the permission mode in HO-02 through HO-06, and HO-06 flagged Bash access for the Code Reviewer. These were recorded as findings and not fixed during the holdouts, because fixing them then would have counted as tuning against the holdout set.

## 3. What did the development rerun, the regression and the holdouts each establish, and what did they fail to establish?

**Development rerun (`CAL-AFTER-001`)**
- *Established:* the fix works. All five functional checks passed, including `tool_authorization` and `lint_command_evidence`.
- *Did not establish:* a passing overall gate. At 59,566 tokens it exceeded the 40,000-token execution-health limit, so it remains an overall deterministic failure and was never scored by the rubric.

**Regression**
- *Established:* the first attempt, `DEV-LINT-001`, **failed** execution health at 74,566 tokens. The second, `CAL-REGRESSION-001`, passed the full deterministic gate (6/6, 39,423 tokens) and scored 12/12 rubric points. It was the first lint run to pass end to end. The distinct task later passed too; see below.
- *Did not establish:* **that the regression used a distinct task.** It reused the calibration lint task, so it does not show that other development work still behaves correctly. There was also **no earlier passing baseline**, so it is a first pass rather than a comparison against a known-good result. With a margin of 577 tokens, and earlier runs of the same task using between 59,566 and 80,738 tokens, the execution-health pass may not be repeatable.

**Distinct regression (`CAL-REGRESSION-DISTINCT-001`, then `CAL-REGRESSION-DISTINCT-002`)**
- *Task:* a regression of the Module 3.1 saved-search `maxPrice` validation task. The Tester ran the `tracker-api` Vitest suite (`npm run test`), which differs from the lint task in package, command and output.
- *Baseline:* `docs/iteration-log.md` records a pre-calibration Tester result of "PASS — 15/15" for this task. That is the only record. No transcript or test output from that run exists in the repository, and git history can't be read here. So "previously passing" rests on documentation, not primary evidence.
- *Attempt 1 (`-001`), established:* the fix generalizes beyond lint **functionally**. With Bash restored, the Tester ran a different validation command with 0 permission denials and reported 15/15 passing with exit code 0. This matches a direct run outside the agent. A separate minimal evaluator profile (`eval/test_deterministic_unit_tests.py`) passed 5 of 6 checks, including tool authorization, test-command evidence and no source writes. The original lint evaluator and all thresholds were left unchanged.
- *Attempt 1 (`-001`), did not establish:* a passing gate. Execution health **failed at 89,854 tokens against the 40,000 limit**, so the rubric judge was correctly not called. Checking the transcript confirmed the figure is real cumulative usage, not an accounting error:
  - The run made 6 API requests, each re-reading cached context of 10,000 to 17,400 tokens, which adds up to 69,954 cache-read tokens.
  - `CAL-REGRESSION-001`, which passed, made 3 requests.
  - With startup memory reads costing about 10,000 tokens, the 40,000-token limit allows only about 3 requests. The token gate therefore measures the number of agent turns as much as the cost of the task.
- *Final scoped attempt (`CAL-REGRESSION-DISTINCT-002`):* this was the single final retry the human approved. The task, agent, grants, evaluator and thresholds were unchanged. Only the prompt was narrowed, to one Bash call with no memory reads, retrieval, git or retries. The Tester ran `npm run test` once and reported exit code 0 and 15/15 passing. The run **passed the deterministic gate (6/6, 22,094 tokens, 10,140 ms, 0 denials) and the rubric (11/12: accuracy 4, coverage 4, recommendation 3)**. Attempt 1's FAIL is kept alongside it.
- *Overall:* the fix generalizes beyond lint, and the distinct task now passes end to end. Two limitations remain:
  - **Baseline:** the "previously passing" baseline is documented only in `docs/iteration-log.md`. No primary pre-calibration evidence exists.
  - **Narrowed prompt:** the pass needed a prompt that skipped the Tester's default memory and retrieval steps. So it shows the task fits the token budget when tightly scoped, not that the Tester's default workflow does.

**Holdouts**
- *Established:* all six holdouts have a post-calibration run in a separate session, with no agent tuning between them. The post-calibration HO-01 run, session `67c33dd5-6361-4af4-8aca-b3ae29889759`, had 5 retrieval attempts, all denied in plan mode, so no lesson citations were produced. Reading the transcripts confirms 10 PASS assertions in HO-02 through HO-06: HO-03 #1, HO-04 #1–2, all four in HO-05, and HO-06 #1, #2 and #4. They also surfaced real gaps:
  - HO-02 conflicts with the approval-gated workflow.
  - HO-03 has a `null` search ID and no successful JSON parse.
  - Retrieval was denied by the permission mode in every post-calibration holdout.
  - HO-06 found a direct read of a confidential lesson and unauthenticated `/debug` endpoints.
- *Did not establish:*
  - **Retrieval in HO-01.** The post-calibration run attempted retrieval but never reached the MCP server, so HO-01 assertions 1–2 FAIL and assertion 3 is NOT VERIFIED. The exploratory run from before calibration (2026-10-27) is kept only as historical evidence.
  - **Independent verification.** All verdicts come from the orchestrator or from reading transcripts. No evaluator script or judge was run on any holdout.
  - **MCP classification-ceiling enforcement** (HO-06 #3). No retrieval request ever reached the server.
  - **The full five-role path in HO-02.** It is BLOCKED at the human-approval checkpoint.

Overall, for the post-calibration runs, 10 of 21 assertions are PASS, 2 FAIL (both HO-01), 4 are BLOCKED and 5 are NOT VERIFIED.

## 4. Was the fix least-privilege, and what orchestration-layer risks remain?

This section adds analysis only. **No agent definition, permission or threshold was changed.** The evidence comes from the transcripts' `init` records and their `permission_denied` events.

**Why the Tester needed Bash, and why restoring it was the right fix**
- The Tester's role is to "run the tests or validation commands relevant to the task" (`.claude/agents/tester.md`). Running `npm run lint` or `npm run test` means running a process. None of `Read`, `Grep`, `Glob` or `mcp__retrieval__retrieve` can do that, so Bash is the only built-in tool that fits.
- The before-fix `init` record shows the grant `Read, Grep, Glob, mcp__retrieval__retrieve`, and `lint_command_evidence` found 0 lint calls. With Bash restored, and nothing else changed, the after-fix `init` includes Bash and the check passed.
- The fix restored exactly the missing capability at the layer where it had been removed: the agent-level `tools:` list. The CLI `--allowedTools` flag had not overridden that list.

**Why broad Bash is a risk**
- `tools: … Bash` grants the whole shell, not just test commands. Leaving out `Edit` and `Write` does not stop file changes. A Bash command can still write or delete files (`>`, `sed -i`, `rm`), change git state, install packages, or make network calls.
- The protections in place today are partial:
  - `permissionMode: plan` applies only when the Tester runs as an orchestrated subagent. There it acts as a read-only filter on commands, and Claude Code denied compound or unverifiable commands: 9 Tester Bash calls in HO-03 (including the JSON parse) and 3 in HO-04.
  - The calibration and regression runs launched the Tester directly with `--permission-mode dontAsk` and `--allowedTools '…Bash…'`. In that mode Bash was unrestricted.
  - The `no_source_writes` check only catches the write tools it lists by name (`Edit`, `Write` and storage writes). **It cannot detect a file write made through Bash.**
  - The role prompt's "do not modify files" is an instruction, not something the system enforces.
- In every post-fix run, the Tester made no write calls and ran only lint, test or inspection commands. That shows how this agent behaved, not that the configuration prevents writes.

**Why the Code Reviewer's Bash is unnecessarily broad**
- A read-only review needs to read and search code, which `Read`, `Grep` and `Glob` already cover. In HO-06 the Code Reviewer used Bash only for `ls`, `grep` and `wc`, all of which those tools can do.
- Its definition relies on the instruction "do not run commands that change the repository or application state", rather than on a missing grant.
- Keeping Bash gives a reviewer the same write-through-shell exposure described above, with no review task that needs it. HO-06 flagged this, and it remains unfixed.

**Why `permissionMode: plan` blocked retrieval even though it was granted**
- `tools:` makes a tool *available* to the agent. `permissionMode` decides whether each call is *allowed*. They are separate controls.
- Every subagent retrieval in the post-calibration holdouts was denied by the mode, not by the MCP server:
  - Planner: 5 in HO-01, 1 in HO-02, 2 in HO-03, 1 in HO-04, 2 in HO-05 and 1 in HO-06.
  - Tester: 2 in HO-03 and 1 in HO-04.
  - Code Reviewer: 1 in HO-06 with the same plan-mode message, and 2 in HO-05 with a generic "Permission … has been denied" message.
  - The typical message is `Cannot call mcp__retrieval__retrieve while in plan mode.` HO-01 records `decision_reason_type: "mode"`.
- **This is an inference, consistent with the evidence:** in plan mode Claude Code allows only operations it can treat as read-only. A third-party MCP tool can't be shown to be read-only from the client side, and a non-interactive subagent can't ask for approval, so the call is refused.
- The same retrieval tool succeeded when the Tester ran in `dontAsk` mode with an explicit `--allowedTools` grant: the lint and distinct-regression runs.
- Because no call reached the server, the per-role MCP limits in `mcp/roles.allowlist.json` (the `internal` classification ceiling) were never exercised under orchestration. In HO-06, the Planner instead opened a `confidential` lesson directly with `Read`, which bypasses that ceiling altogether.

**What a future least-privilege configuration should restrict.** These are *proposals*. **None of them is implemented.**
1. **Tester:** limit Bash to the validation commands it needs, using command-scoped permission rules, for example `npm run lint` and `npm run test` in their package directories only. Deny everything else, including redirection, `rm`, `git` writes and package installs.
2. **Code Reviewer:** remove Bash entirely and rely on `Read`, `Grep` and `Glob`.
3. **Retrieval under orchestration:** explicitly allow `mcp__retrieval__retrieve` for the Planner, Tester and Code Reviewer, through a permission allow rule or a different permission mode for those roles. That way the step their definitions require can run, and the server's role and classification checks are actually exercised.
4. **Reference files:** deny direct `Read` access to `.memory/reference/` for agent roles, so classified lessons can only be reached through the MCP server's ceiling.
5. **`no_source_writes` check:** extend it, or add a separate check, to detect file changes made through Bash, for example by comparing the working tree before and after a run.

**Why these changes were deferred**
- The calibration cycle requires the holdouts to be measured on a frozen configuration, with no tuning between runs.
- Changing grants or permission modes after seeing holdout results would tune the system against the holdout set, and would make HO-01 to HO-06 measure a different configuration from the one that was calibrated.
- The calibration fix was therefore limited to the one fault the development runs diagnosed. The issues above are recorded as findings.
- Applying them belongs in a new, separately labelled cycle: change the configuration, re-run the development checks and the holdouts, and keep the results separate from this cycle's.
