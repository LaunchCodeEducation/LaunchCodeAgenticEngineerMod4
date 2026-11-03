# Module 3.3 Exercise 1 — Written answers

## Question 1

I used deterministic checks for facts that can be verified from saved execution evidence: the expected Tester-only development route and execution count; the existence of a valid Claude Code JSONL transcript with initialization and completion records; the exact tool grants, actual tool calls, and absence of permission denials; a real `npm run lint` Bash invocation with a returned tool response; the absence of source or persistent-storage write tools in a read-only verification task; and successful execution within defined time and token budgets. These are appropriate for pass-or-fail evaluation because each requirement has an observable condition, rather than depending on an opinion about the quality of the agent's explanation. The suite fails closed when evidence is missing and identifies the associated risk and explanation. The routing check applies to this small development lint task; other orchestration paths need separately configured checks.

## Question 2

The rubric evaluates the *quality* of the lint summary: whether the agent accurately interprets the observed lint result, covers the important errors and warnings, and recommends a useful next step. These require judgment about completeness, relevance, and usefulness that a simple schema or tool-call check cannot establish. Both layers remain limited by the coverage and integrity of the saved evidence. A single development task cannot establish reliability across other tasks, multi-agent handoffs, adversarial inputs, long-running failures, or all possible authorization boundaries. The manifest also cannot independently authenticate an agent's role without stronger instrumentation. Real holdout and failure-injection tests are still necessary later.

## Question 3

High rubric scores support the limited conclusion that, for the specific recorded task and evidence, the judge found the lint summary accurate, comprehensive, and actionable under the Module 1 criteria. If the deterministic gate also passed, the run additionally met the specific structural checks included in this harness. It would be unsafe to conclude that the system is universally correct, secure, reliably orchestrated across all five agents, free from context bleed, or ready for production. A judge can make mistakes, and passing scores do not cover untested tasks or missing instrumentation. Quality scores must not be treated as substitutes for deterministic authorization, audit, routing, or tool-result evidence.

## Verification note

The uploaded project ZIP excluded raw agent transcripts, so a genuine development-run result and live judge scores **cannot be claimed from the ZIP alone**. The included synthetic fixture and mocked judge verify integration, not agent performance. Run the documented authenticated development task and record the actual reports before representing the baseline as complete.
